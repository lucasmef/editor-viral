// Scene-local half-open frame intervals. Pixel units refer to the cached alpha.
export type HairAlpha = {
  black?:number; white?:number; gamma?:number; offsetPx?:number; featherPx?:number;
  featherMode?:'outward'|'symmetric'; protectOpaque?:boolean;
};
export type HairBackground = {
  donorOffsetNative?:[number,number]; gainRgb?:[number,number,number];
  offsetRgb?:[number,number,number]; featherPx?:number; patchOffsetPx?:[number,number];
};
export type HairRange = {from:number; to:number; fadeFrames?:number};
export type HairAdjustment = {alpha?:HairAlpha; intensity?:number};
export type HairScene = HairAdjustment & {
  background?:HairBackground; intervals?:(HairRange & HairAdjustment)[]; bypass?:HairRange[];
};
export type HairControls = {
  schemaVersion:1; cacheId:string;
  defaults:HairAdjustment & {background?:HairBackground}; scenes:Record<string,HairScene>;
};
export type HairFinishing = {
  version:'editor-hair-v1'; enabled:boolean; python:string;
  cache:{path:string; sha256:string; cacheId:string}; controls:HairControls;
  output?:{mediaId:`m-${string}`; work:string; stageSha256:string; quality:'preview'|'production'};
};
