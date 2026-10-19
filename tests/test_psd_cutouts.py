import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import psd_cutouts as p
from psd_tools.api.layers import PixelLayer

class PSDTests(unittest.TestCase):
 def test_mask_roundtrip_recovers_original_pixels_and_native_canvas(self):
  with tempfile.TemporaryDirectory() as base:
   d=Path(base);im=p.Image.new('RGB',(80,100),'red');doc=p.PSDImage.new('RGB',im.size);doc.append(PixelLayer.frompil(im,doc,'original'));doc.save(d/'source.psd')
   mask=p.Image.new('L',im.size,255);mask.paste(0,(0,0,40,100));mask.save(d/'mask.png')
   before=p.sha(d/'source.psd');report=p.mask_layer(d/'source.psd',[0],d/'mask.png',d/'masked.psd')
   self.assertTrue(report['mergedTransparencyFlagVerified']);self.assertFalse(report['photoshopOpenVerified']);self.assertTrue(report['originalPixelsRetained']);self.assertEqual(p.sha(d/'source.psd'),before)
   reopened=p.PSDImage.open(d/'masked.psd');self.assertEqual(reopened[0].topil().getpixel((10,10))[:3],(255,0,0))
   self.assertEqual(reopened.topil(channel=p.ChannelID.TRANSPARENCY_MASK).getpixel((10,10)),0)
   # Independent Pillow PSD decoder verifies the merged stream is readable.
   with p.Image.open(d/'masked.psd') as independent:
    independent.load();self.assertEqual(independent.size,(80,100))
   self.assertEqual(reopened._record.layer_and_mask_information.layer_info.layer_count,-1)
   p.export_png(d/'masked.psd',d/'view.png')
   with p.Image.open(d/'view.png') as png:self.assertEqual(png.size,(80,100));self.assertEqual(png.getpixel((10,10))[3],0)
   # Reveal previously hidden pixels by replacing the mask, without regenerating color.
   p.Image.new('L',im.size,255).save(d/'all.png');p.mask_layer(d/'masked.psd',[0],d/'all.png',d/'recovered.psd')
   self.assertEqual(p.PSDImage.open(d/'recovered.psd')[0].topil().tobytes(),reopened[0].topil().tobytes())
 def test_never_overwrites_source(self):
  with self.assertRaisesRegex(ValueError,'new version'):p.mask_layer(__file__,[0],__file__,__file__)
