import contextlib
import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import click


@click.group()
@click.pass_context
def update(ctx):
    ctx.ensure_object(dict)
    with open('baseline.json', 'r') as f:
        ctx.obj['baseline'] = json.load(f)


@update.command()
@click.option('-m', '--major', required=True, type=click.Choice(['general', 'cs', 'isee', 'math', 'physics', 'se']))
@click.option('-d', '--degree', required=True, type=click.Choice(['undergraduate', 'graduate']))
@click.option('-t', '--thesis_type', required=True, type=click.Choice(['thesis', 'design']))
@click.option('-p', '--period', required=True, type=click.Choice(['proposal', 'final']))
@click.option('-b', '--blind', is_flag=True)
@click.option('-l', '--grad_level', required=True, default='master', type=click.Choice(['master', 'doctor']))
@click.pass_context
def single(ctx, major, degree, thesis_type, period, blind, grad_level):
    '''Update single baseline pdf file'''
    update_single(ctx, major, degree, thesis_type, period, blind, grad_level)


@update.command()
@click.pass_context
def preset(ctx):
    '''Update preset baseline pdf files'''
    pass


def update_single(ctx, major, degree, thesis_type, period, blind, grad_level):
    # Single pdf config
    curr_cfg = dict()

    # Output filename
    filename = f'zjuthesis-{degree}-{grad_level}-{grad_level}-{major}-{thesis_type}-{period}'
    if blind:
        filename += f'-blind'
    filename += f'.pdf'
    curr_cfg['filename'] = filename

    # Texlive
    tl = texlive()
    curr_cfg['texlive'] = tl.get_config()

    # Git clone zjuthesis
    curr_time = datetime.utcnow()
    curr_cfg['time'] = curr_time.isoformat()
    sub_dir = f'zjuthesis-{curr_time.isoformat()}'
    with chmkdir(Path('.') / 'out'):
        run(['git', 'clone', '--depth=1', 'git@github.com:thenetadmin/zjuthesis', sub_dir])
    with chdir(Path('.') / 'out' / sub_dir):
        curr_cfg['zjuthesis'] = dict()
        curr_cfg['zjuthesis']['commit_id'] = run(
            ['git', 'rev-parse', '--short', 'HEAD'])
        curr_cfg['zjuthesis']['major'] = major
        curr_cfg['zjuthesis']['degree'] = degree
        curr_cfg['zjuthesis']['thesis_type'] = thesis_type
        curr_cfg['zjuthesis']['period'] = period
        curr_cfg['zjuthesis']['blind'] = blind
        curr_cfg['zjuthesis']['grad_level'] = grad_level
    

    print(curr_cfg)


@contextlib.contextmanager
def chmkdir(path):
    """Go to working directory and return to previous on exit."""
    prev_cwd = Path.cwd()
    Path(path).mkdir(parents=True, exist_ok=True)
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)


@contextlib.contextmanager
def chdir(path):
    """Go to working directory and return to previous on exit."""
    prev_cwd = Path.cwd()
    Path(path)
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)


def run(cmd: list, capture_output=True):
    try:
        return subprocess.run(cmd, capture_output=capture_output,
                              check=True).stdout.decode('utf-8').strip()
    except subprocess.CalledProcessError:
        subprocess.run(cmd, check=True)


class texlive:
    def __init__(self):
        pass

    def get_config(self) -> dict:
        cfg = dict()
        cfg['type'] = 'docker@adnrv/texlive:full'
        res = run(['docker', 'run', '--rm', 'adnrv/texlive:full',
                  'latexmk', '--version'])
        cfg['latexmk'] = res
        res = run(['docker', 'run', '--rm', 'adnrv/texlive:full',
                  'xelatex', '--version'])
        cfg['xelatex'] = res.split('\n')[0]
        return cfg

    def compile(self, dir):
        pass


if __name__ == '__main__':
    update()
