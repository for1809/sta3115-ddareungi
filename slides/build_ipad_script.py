"""Create an iPad reading copy of work/presentation-script.html.

Run from the project root: python -B slides/build_ipad_script.py
The output can be read directly or printed to PDF. No spoken text is changed.
"""
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'work/presentation-script.html'
OUT = ROOT / 'work/presentation-script-ipad.html'

STYLE = """
*{box-sizing:border-box}
body{margin:0;background:#e9edf2;color:#17202b;font-family:Arial,sans-serif}
.page{width:768px;height:1024px;margin:24px auto;padding:44px 48px;background:#fff;display:flex;flex-direction:column;break-after:page}
.page:last-child{break-after:auto}
.page-header{flex-shrink:0;margin-bottom:22px}
.slide-number{font-size:18px;font-weight:bold;color:#2763b6;margin:0 0 12px}
h1{font-size:32px;line-height:1.16;margin:0 0 10px}
.timing{font-size:17px;color:#617080;margin:0}
.cue{flex-shrink:0;font-size:18px;line-height:1.35;color:#42566f;background:#f0f5fc;padding:12px 15px;margin:0 0 22px}
.speech-area{flex:1;min-height:0}
.speech{font-size:26px;line-height:1.43}
.speech p{margin:0 0 14px}.speech p:last-child{margin-bottom:0}
.page-footer{flex-shrink:0;font-size:15px;color:#74808d;margin-top:18px}
@page{size:768px 1024px;margin:0}
@media print{body{background:#fff}.page{margin:0}*{print-color-adjust:exact;-webkit-print-color-adjust:exact}}
@media screen and (max-width:800px){body{background:#fff}.page{width:100%;height:auto;min-height:100vh;margin:0;padding:32px 28px;border-bottom:1px solid #dce3eb}.speech{font-size:26px!important}.speech-area{flex:none}.page-footer{margin-top:28px}}
"""

FIT_SCRIPT = """
function fitPages(){
  document.querySelectorAll('.page').forEach(page=>{
    const area=page.querySelector('.speech-area'),speech=page.querySelector('.speech');
    let size=26;speech.style.fontSize=size+'px';
    if(matchMedia('print').matches || innerWidth>800){
      while(speech.getBoundingClientRect().height>area.clientHeight && size>20){
        size-=.5;speech.style.fontSize=size+'px';
      }
      page.dataset.overflow=String(speech.getBoundingClientRect().height>area.clientHeight+1);
    }
    page.dataset.fontSize=String(size);
  });
}
addEventListener('load',fitPages);addEventListener('resize',fitPages);addEventListener('beforeprint',fitPages);
"""


def build():
    source = SOURCE.read_text()
    sections = list(re.finditer(r'<section data-slide="(\d+)" data-id="([^"]+)">(.*?)</section>', source, re.S))
    assert len(sections) == 19
    pages = []
    for section in sections:
        number, sid, content = section.groups()
        heading = re.search(r'<h2>(.*?)<span class="timing">(.*?)</span></h2>', content, re.S)
        title = re.sub(r'^\d+\s*·\s*', '', heading[1].strip())
        cue = re.search(r'<p class="cue">(.*?)</p>', content, re.S)
        cue_markup = '<p class="cue">' + cue[1] + '</p>' if cue else ''
        spoken = re.findall(r'<p class="spoken">(.*?)</p>', content, re.S)
        speech = ''.join('<p>' + text + '</p>' for text in spoken)
        pages.append(f'<article class="page" data-id="{sid}"><header class="page-header">'
                     f'<p class="slide-number">SLIDE {number} / {len(sections)}</p>'
                     f'<h1>{title}</h1><p class="timing">{heading[2]}</p></header>'
                     + cue_markup + '<div class="speech-area"><div class="speech">' + speech + '</div></div>'
                     '<footer class="page-footer">Exploring Bicycle Imbalances · Group 1</footer></article>')
    output = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
              '<meta name="viewport" content="width=device-width,initial-scale=1">'
              '<title>iPad presentation script</title><style>' + STYLE + '</style></head><body>'
              + '\n'.join(pages) + '<script>' + FIT_SCRIPT + '</script></body></html>')
    assert sum(len(re.findall(r'\S+', html.unescape(x))) for x in re.findall(r'<p class="spoken">(.*?)</p>', source, re.S)) > 1700
    OUT.write_text(output)
    print(f'{len(pages)} pages -> {OUT}')


if __name__ == '__main__':
    build()
