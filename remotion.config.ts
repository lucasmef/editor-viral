import {Config} from '@remotion/cli/config';
import storage from './studio/storage.json';
import path from 'node:path';
import fs from 'node:fs';
const roots = process.env.EDITOR_STORAGE_CONFIG ? JSON.parse(fs.readFileSync(process.env.EDITOR_STORAGE_CONFIG, 'utf8')).roots : storage.roots;
// Media staging and Webpack artifacts belong to the external cache.
Config.setPublicDir(path.join(roots.cache, 'staging'));
Config.overrideWebpackConfig((config) => ({...config, cache: config.cache && typeof config.cache === 'object' ? {...config.cache, cacheDirectory: path.join(roots.cache,'webpack')} : config.cache}));
