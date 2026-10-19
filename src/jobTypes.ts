import type {Caption, Layer, Project} from './types';
import type {HairFinishing} from './hairTypes';

// Editable schema. Times use the project's fps and are local to each scene.
export type MediaId = `m-${string}`;
export type Clip = {mediaId:MediaId;inFrame:number;proxy?:{mediaId:MediaId;inFrame:number;sourceInFrame:number}};
export type EventAnchor = {id:string;kind:'word'|'gesture';frame:number};
export type JobLayer = Omit<Layer,'src'> & {mediaId:MediaId|null;premiereMediaId?:MediaId;anchor?:string;offsetFrames?:number};
export type JobScene = {id:string;script:string;duration:number;clip:Clip;layers:JobLayer[];captions:Caption[];events:EventAnchor[];looks?:{id:string;label?:string;layerIds:string[]}[];origin?:Record<string,unknown>};
export type EditJob = {schemaVersion:2;videoId:string;width:number;height:number;fps:number;scenes:JobScene[];requireLookReview?:boolean;parent?:{job:string;revision:string}};
export type StyleProfile = {premiereCaptionPosition?:[number,number];version:string;layout:Project['layout'];captionPolicy:{mode:'word'|'group';omit:string[];preserve?:string[];punctuation:boolean;compounds?:string[]}};
export type VoiceProfile = {enabled:boolean;version:string;bundle:string;manifestSha256:string;approvalSha256:string;approvalFingerprint:string};
export type Finishing = {windows?:{work:string;sealSha256:string;videoMediaId:MediaId};audioGainDb:number;soundEffects?:{mediaId:MediaId;scene:string;frame:number;duration:number;gainDb:number}[];colorGrade?:Project['colorGrade'];hair?:HairFinishing;voiceNeural?:VoiceProfile;audioConnector?:{kind:'editor-voice-neural-v1';binding:{editHash:string;profile:VoiceProfile;adapterSha256:string};report:string;reportSha256:string};audioMediaId?:MediaId;videoMediaId?:MediaId;audioEditHash?:string;videoEditHash?:string;audioNotes?:string;videoNotes?:string;videoConnector?:{kind:'editor-face-metal-v1';work:string;binding:Record<string,unknown>;reportSha256:string;temporalReview:string;temporalReviewSha256:string};retouch?:string;color?:string};
