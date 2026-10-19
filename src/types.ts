export type Rect = {x:number;y:number;width:number;height:number};
export type Shot = {src:string;inFrame:number;outFrame:number;from:number};
export type Caption = {text:string;from:number;duration:number;highlight?:boolean};
export type CutoutProvenance = {
 assetSha256?:string;pngSha256?:string;original:{path:string;sha256:string;pixelSize:[number,number]};
 resampled:false;canvasCrop?:[number,number,number,number];
 recovery: {kind:'separate-mask';pixels:{path:string;sha256:string};mask:{path:string;sha256:string}} |
 {kind:'layered-psd';document:{path:string;sha256:string};inspection:{path:string;sha256:string}};
};
export type Layer = {premiereSrc?:string;cutoutProvenance?:CutoutProvenance;native?:{props:Record<string,any>};id:string;src:string|null;label:string;color:string;from:number;duration:number;rect:Rect;crop?:Rect & {imageWidth:number;imageHeight:number};clipPath?:string;transition:'cut'|'fade';fadeFrames:number};
export type Scene = {id:string;from:number;duration:number;script:string;layers:Layer[]};
export type Project = {
 editorialMode?:'fashion'|'no-looks';
 premiereCaptionPosition?:[number,number];schemaVersion:1;videoId:string;width:number;height:number;fps:number;durationInFrames:number;
 timingStatus:'draft'|'reviewed';source:string|null;shots:Shot[];
 previewGuides?:{safeInset:number;lookTop?:number;lookBottom?:number}|null;
 audioSrc?:string;audioGainDb?:number;
 soundEffects?:{src:string;from:number;duration:number;gainDb:number}[];
 colorGrade?:{brightness?:number;contrast?:number;saturation?:number;warmth?:number};
 layout:{safeMargin?:number;lookGuides?:{top:number;bottom:number};base?:{scale:number;x:number;y:number};revealOverlaysWithLooks?:boolean;labels:{text:string;x:number;y:number;bubble?:boolean;src?:string;mediaId?:string;width?:number;height?:number;crop?:Rect & {imageWidth:number;imageHeight:number};fontSize?:number;fontFamily?:string;fontWeight?:number;color?:string;strokeWidth?:number}[];caption:{x:number;y:number;width:number;fontSize:number;fontFamily?:string;fontWeight?:number;strokeWidth?:number;highlight?:'underline'|'pill'|'scale'|'glow';accentColor?:string}};
 scenes:Scene[];captions:Caption[];
 reviews:Record<string,{status:'pending'|'passed';evidence:string|null}>;
};
