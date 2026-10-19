// Local patch for premiere-pro-mcp 1.24.0. No new server or unsafe-script tool.
// Return an ES3 body for the existing project-guarded bridge.
export function safeMoveScript(nodeId, startSeconds, targetIndex) {
 return `
var id = ${JSON.stringify(nodeId)}, seconds = ${startSeconds}, destination = ${targetIndex};
function refuse(message) { return __error(message, {outcome:"not_applied",verified:false,timelineChanged:false}); }
var seq = app.project.activeSequence;
if (!seq) return refuse("No active sequence; nothing changed.");
var found = __findClip(id);
if (!found) return refuse("Clip not found; nothing changed.");
var kind = found.trackType, origin = found.trackIndex, item = found.clip;
var tracks = kind === "video" ? seq.videoTracks : seq.audioTracks;
if (destination >= tracks.numTracks) return refuse("Target track out of range; nothing changed.");
var frame = Number(seq.timebase), oldStart = Number(item.start.ticks), oldEnd = Number(item.end.ticks);
if (!(frame > 0) || !(oldEnd > oldStart)) return refuse("Unreadable frame grid or range; nothing changed.");
var start = __snapSequenceTicks(seq, __secondsToTicks(seconds)), end = start + oldEnd - oldStart;
if (Math.abs(oldStart / frame - Math.round(oldStart / frame)) > .001 || Math.abs(oldEnd / frame - Math.round(oldEnd / frame)) > .001)
 return refuse("Clip is off the sequence frame grid; nothing changed.");
try {
 var links = item.getLinkedItems();
 for (var l = 0; links && l < links.numItems; l++)
  if (String(links[l].nodeId) !== id) return refuse("Linked clip moves require a separately validated group operation; nothing changed.");
} catch (linkError) { return refuse("Could not inspect linked items; nothing changed."); }
function trackSafe(t) {
 try { return !t.isLocked() && (!t.transitions || t.transitions.numItems === 0); }
 catch (e) { return false; }
}
function free(t, left, right) {
 if (!trackSafe(t)) return false;
 for (var c = 0; c < t.clips.numItems; c++) {
  var other = t.clips[c];
  if (String(other.nodeId) !== id && Number(other.start.ticks) < right && Number(other.end.ticks) > left) return false;
 }
 return true;
}
var low = Math.min(oldStart, start), high = Math.max(oldEnd, end), route = "" , staging = -1;
if (!trackSafe(tracks[origin]) || !free(tracks[destination], start, end))
 return refuse("Destination occupied, locked, or has transitions; nothing changed.");
if (origin === destination) {
 if (!free(tracks[origin], low, high)) return refuse("Time move crosses another clip; nothing changed.");
 route = "same_track";
} else if (free(tracks[origin], low, high)) route = "time_then_track";
else if (free(tracks[destination], low, high)) route = "track_then_time";
else {
 for (var t = 0; t < tracks.numTracks; t++)
  if (t !== origin && t !== destination && free(tracks[t], low, high)) { staging = t; break; }
 if (staging < 0) return refuse("No collision-free route. Add an empty unlocked track and retry; nothing changed.");
 route = "via_free_track";
}
// Capture every A/V clip, not only the one requested. Refuse unreadable data.
// The moved clip must be static: keyframe time semantics are not proven by this patch.
function snapshot() {
 var out = {}, count = 0, props = 0;
 for (var k = 0; k < 2; k++) {
  var collection = k === 0 ? seq.videoTracks : seq.audioTracks;
  for (var t = 0; t < collection.numTracks; t++) for (var c = 0; c < collection[t].clips.numItems; c++) {
   var clip = collection[t].clips[c], key = String(clip.nodeId), effects = [];
   if (++count > 500 || out[key]) throw new Error("Snapshot clip limit or duplicate ID");
   for (var e = 0; e < clip.components.numItems; e++) {
    var component = clip.components[e], parameters = [];
    for (var p = 0; p < component.properties.numItems; p++) {
     if (++props > 10000) throw new Error("Snapshot property limit");
     var param = component.properties[p], animated = param.isTimeVarying(), keys = [];
     if (animated && key === id) throw new Error("Animated moved clip requires separate keyframe validation");
     if (animated) {
      var times = param.getKeys();
      for (var q = 0; times && q < times.length; q++) {
       if (++props > 10000) throw new Error("Snapshot keyframe limit");
       keys.push([String(times[q].ticks), param.getValueAtKey(times[q])]);
      }
     }
     parameters.push([param.displayName, param.getValue(), animated, keys]);
    }
    effects.push([component.matchName, component.displayName, parameters]);
   }
   out[key] = {trackType:k === 0 ? "video" : "audio", trackIndex:t,
    start:String(clip.start.ticks), end:String(clip.end.ticks),
    inPoint:String(clip.inPoint.ticks), outPoint:String(clip.outPoint.ticks),
    name:clip.name, source:clip.projectItem ? String(clip.projectItem.nodeId) : null,
    disabled:clip.disabled, speed:clip.getSpeed(), reversed:clip.isSpeedReversed(), effects:effects};
  }
 }
 return out;
}
var baseline;
try { baseline = snapshot(); } catch (e) { return refuse("Cannot verify preservation: " + e.toString() + "; nothing changed."); }
function check(expectedTrack, expectedStart, expectedEnd) {
 var actual = snapshot(), expected = {}, key;
 for (key in baseline) expected[key] = baseline[key];
 var moved = {}, source = baseline[id];
 for (key in source) moved[key] = source[key];
 moved.trackIndex = expectedTrack; moved.start = String(expectedStart); moved.end = String(expectedEnd); expected[id] = moved;
 var n = 0, m = 0;
 for (key in expected) { n++; if (!actual[key] || __jsonStringify(actual[key]) !== __jsonStringify(expected[key])) throw new Error("Clip preservation mismatch: " + key); }
 for (key in actual) m++;
 if (m !== n) throw new Error("Clip count changed");
 return n;
}
function timeMove(newStart, newEnd) {
 var current = __findClip(id);
 if (!current) throw new Error("Moving clip disappeared");
 if (Number(current.clip.start.ticks) !== newStart || Number(current.clip.end.ticks) !== newEnd)
  __writeClipSpan(current.clip, newStart, newEnd);
 check(current.trackIndex, newStart, newEnd);
}
function trackMove(to) {
 var current = __findClip(id);
 if (!current) throw new Error("Moving clip disappeared");
 var left = Number(current.clip.start.ticks), right = Number(current.clip.end.ticks);
 if (!free(tracks[to], left, right)) throw new Error("Intermediate destination is no longer free");
 app.enableQE(); var qeSeq = qe.project.getActiveSequence();
 var qt = kind === "video" ? qeSeq.getVideoTrackAt(current.trackIndex) : qeSeq.getAudioTrackAt(current.trackIndex);
 var qc = null;
 for (var q = 0; q < qt.numItems; q++) {
  var candidate = qt.getItemAt(q);
  if (candidate && String(candidate.type) === "Clip" && Number(candidate.start.ticks) === left) {
   if (qc) throw new Error("Ambiguous QE clip"); qc = candidate;
  }
 }
 if (!qc) throw new Error("QE clip not found");
 qc.moveToTrack(kind === "video" ? to-current.trackIndex : 0, kind === "audio" ? to-current.trackIndex : 0, "0", false);
 check(to, left, right);
}
try {
 if (route === "same_track") timeMove(start, end);
 else if (route === "time_then_track") { timeMove(start, end); trackMove(destination); }
 else if (route === "track_then_time") { trackMove(destination); timeMove(start, end); }
 else { trackMove(staging); timeMove(start, end); trackMove(destination); }
 var checked = check(destination, start, end);
 return __result({moved:true, verified:true, outcome:"verified", route:route, stagingTrack:staging,
  clipName:baseline[id].name, newStart:__ticksToSeconds(start), newEnd:__ticksToSeconds(end),
  trackIndex:destination, preservedClipCount:checked, preservation:"All A/V clip IDs, source/ranges, speed, enabled state and readable component values/keyframes compared after each step. Moved animated clips, linked clips and transition-bearing route tracks are refused."});
} catch (e) {
 return __error("Move stopped: " + e.toString() + ". Inspect the sequence before further editing; no automatic rollback was attempted.", {outcome:"committed_unverified",verified:false,timelineChanged:null});
}
`;
}
