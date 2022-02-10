
import os
import json
import random
import argparse
from collections import ChainMap

from flask import Flask, abort
app = Flask(__name__)

NB_RAW = 5
NB_COL = 5
NB_CELL = NB_RAW * NB_COL

BINGO_DIR = 'bingos/'
STAT_FILE = 'stats.json'
RESOURCE_PATH = 'https://bingo.bourneuf.net/part'
RESOURCE_PATH = 'https://www.buzzwordbingogame.com/parts'

def parse_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('jsonfile', type=str, help='json file containing the bingo to generate')
    parser.add_argument('resource-path', nargs='?', type=str, help='path where to find style sheets and js', default=RESOURCE_PATH)
    return parser.parse_args()

MODEL = """
<!--  custom ---><!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
    <meta name="apple-mobile-web-app-capable" content="yes" />
    <meta name="description" content="Forget the cheap imitations, this is the original web based, randomly generated, buzzword bingo game!" />
    <meta name="keywords" content="bingo" />
    <meta name="viewport" content="width=750">
    <title>{title}</title>
    <link type="text/plain" rel="author" href="{res_path}/humans.txt" />
    <link rel="shortcut icon" href="{res_path}/favicon.ico" type="image/ico" />
    <link rel="icon" href="{res_path}/favicon.ico" />
    <link rel="apple-touch-icon" href="{res_path}/img/bsbingo.png"
      type="image/png" />
    <link rel="stylesheet" type="text/css" href="{res_path}/css/style.css" />
    <link rel="image_src" href="{res_path}/img/bsbingo.png" />
    <script type="text/javascript" src="{res_path}/js/game.js" async></script>
  </head>
  <body>
    <h1>{title}</h1>
    <center><h3>Criez <b>«{shout}»</b> quand vous obtenez une ligne ou une colonne !</h3><center>
    <br/>
    <table class="card" id="card0" border="1" cellspacing="0">
      {table}
    </table>
    <br/>
    <br/>
    <center><small>Interface collectivisée depuis <a href="https://www.buzzwordbingogame.com">buzzwordbingogame.com</a></small></center>
  </body>
</html>
"""


def get_bingo(jsonfile) -> dict:
    with open(jsonfile) as fd:
        config = ChainMap(json.load(fd), {'shout': 'ROUFLAQUETTES !', 'title': 'bingo'})
    return config['title'], config['shout'], tuple(config['words'])


def yield_table(words:list) -> [str]:
    if len(words) == 0: raise NotImplementedError("No word provided.")
    while len(words) < NB_CELL:
        words *= 2
    words = iter(random.sample(words, NB_CELL))
    for _ in range(NB_RAW):
        yield '<tr>'
        for _ in range(NB_COL):
            yield f'<td>{next(words)}</td>'
        yield '</tr>'


def generate_bingo(jsonfile, resource_path:str):
    title, shout, words = get_bingo(jsonfile)
    html = MODEL.format(res_path=resource_path, title=title, shout=shout, table=''.join(yield_table(words)))
    return html

def save_stats(bingo_uid):
    try:
        with open(STAT_FILE) as fd:
            stats = json.load(fd)
    except:
        stats = {}

    stats.setdefault(bingo_uid, 0)
    stats[bingo_uid] += 1

    with open(STAT_FILE, 'w') as fd:
        json.dump(stats, fd)


@app.route('/<bingo>')
def return_bingo(bingo:str):
    fname = os.path.join(BINGO_DIR, bingo + '.json')
    if os.path.exists(fname):
        save_stats(bingo)
        return generate_bingo(fname, RESOURCE_PATH)
    abort(404)


@app.route('/')
def return_bingo_list():
    if os.path.exists(STAT_FILE):
        with open(STAT_FILE) as fd:
            stats = json.load(fd)
    else:
        stats = {}
    if stats:
        header = ' <tr> <th>bingo</th> <th>nombres de grilles générées</th> </tr>\n'
        lines = '\n'.join(
            f' <tr> <td><a href="/{bingo}">{bingo}</a></td> <td>{hits}</td> </tr>\n'
            for bingo, hits in stats.items()
        )
        html = '<table>' + header + lines + '</table>'
    else:
        html = 'No bingo used for now'
    return html
