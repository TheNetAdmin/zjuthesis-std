import contextlib
import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import click


@click.group()
def update():
    pass


@update.command()
@click.option('-d', '--degree', required=True, type=click.Choice(['undergraduate', 'graduate']))
@click.option('-m', '--major', required=True, type=click.Choice(['general', 'cs', 'isee', 'math', 'physics', 'se']))
@click.option('-t', '--thesis_type', required=True, type=click.Choice(['thesis', 'design']))
@click.option('-p', '--period', required=True, type=click.Choice(['proposal', 'final']))
@click.option('-b', '--blind', is_flag=True)
@click.option('-g', '--grad_level', required=True, default='master', type=click.Choice(['master', 'doctor']))
@click.option('-l', '--language', required=True, default='chinese', type=click.Choice(['chinese', 'english']))
def single(degree, major, thesis_type, period, blind, grad_level, language):
    '''Update single baseline pdf file'''
    update_single(degree, major, thesis_type,
                  period, blind, grad_level, language)


@update.command()
def preset():
    '''Update preset baseline pdf files'''
    # 1. Undergraduate
    major_main = ['general', 'cs']
    major_sample = ['isee', 'math', 'physics']
    thesis_type = ['thesis']
    periods = ['final', 'proposal']
    
    # Blind Review
    update_single('undergraduate', 'general', 'thesis', 'final', True)
    # Main Majors
    for m in major_main:
        for t in thesis_type:
            for p in periods:
                update_single('undergraduate', m, t, p, False)
    # CS Design Final and Proposal
    update_single('undergraduate', 'cs', 'design', 'final', False)
    update_single('undergraduate', 'cs', 'design', 'proposal', False)
    # Sample Majors
    for m in major_sample:
        update_single('undergraduate', m, 'thesis', 'final', False)
    # 2. Graduate
    update_single('graduate', 'cs', 'thesis', 'final', False, 'master')
    update_single('graduate', 'general', 'thesis', 'final', False, 'master')
    update_single('graduate', 'general', 'thesis', 'final', False, 'doctor')
    update_single('graduate', 'general', 'thesis', 'final', False, 'doctor', 'english')


def update_single(degree, major, thesis_type, period, blind, grad_level = 'doctor', language = 'chinese'):
    assert degree in ['undergraduate', 'graduate']
    assert major in ['general', 'cs', 'isee', 'math', 'physics', 'se']
    assert thesis_type in ['thesis', 'design']
    assert period in ['proposal', 'final']
    assert grad_level in ['master', 'doctor']
    assert language in ['chinese', 'english']
    # Single pdf config
    with open('baseline.json', 'r') as f:
        cfg = json.load(f)

    # Output filename
    filename = f'zjuthesis-{degree}'
    if degree == 'graduate':
        filename += f'-{grad_level}'
    filename += f'-{major}-{thesis_type}-{period}'
    if blind:
        filename += f'-blind'
    if language != 'chinese':
        filename += f'-{language}'
    filename += f'.pdf'

    # Prev config
    curr_cfg = dict()
    prev_cfg = cfg[filename] if filename in cfg.keys() else None

    # Texlive
    tl = texlive()
    curr_cfg['texlive'] = tl.get_config()

    # Git clone zjuthesis
    curr_time = datetime.utcnow()
    curr_cfg['time'] = curr_time.isoformat()
    sub_dir = f'zjuthesis-{curr_time.isoformat()}'
    baseline_dir = Path('.').resolve()
    with chmkdir(baseline_dir / 'out'):
        run(['git', 'clone', '--depth=1',
            'git@github.com:thenetadmin/zjuthesis', sub_dir], capture_output=False)
    with chdir(baseline_dir / 'out' / sub_dir):
        curr_cfg['zjuthesis'] = dict()
        curr_cfg['zjuthesis']['commit_id'] = run(
            ['git', 'rev-parse', '--short', 'HEAD'])
        if prev_cfg and prev_cfg['zjuthesis']['commit_id'] == curr_cfg['zjuthesis']['commit_id']:
            print(
                f'Commit ID {curr_cfg["zjuthesis"]["commit_id"]} matches previous record, skip {filename}')
            return
        curr_cfg['zjuthesis']['major'] = major
        curr_cfg['zjuthesis']['degree'] = degree
        curr_cfg['zjuthesis']['thesis_type'] = thesis_type
        curr_cfg['zjuthesis']['period'] = period
        curr_cfg['zjuthesis']['blind'] = blind
        curr_cfg['zjuthesis']['grad_level'] = grad_level
        curr_cfg['zjuthesis']['language'] = language
        run(['bash', 'script/ci/setup.sh'], capture_output=False)
        tl.compile(Path('.'), curr_cfg['zjuthesis'])
        new_pdf = Path('.') / 'dist' / filename
        new_pdf.rename(baseline_dir/filename)

    cfg[filename] = curr_cfg
    with open('baseline.json', 'w') as f:
        json.dump(cfg, f, indent=4)


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
        if capture_output:
            return subprocess.run(cmd, capture_output=True,
                                  check=True).stdout.decode('utf-8').strip()
        else:
            subprocess.run(cmd, check=True)
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

    def compile(self, path: Path, cfg: dict):
        cmd = []
        cmd += ['docker', 'run']
        cmd += ['--user', '1000:1000']
        cmd += ['--mount', f'src={path.resolve()},target=/zjuthesis,type=bind']
        cmd += ['--rm', 'adnrv/texlive:full']
        cmd += ['bash', '/zjuthesis/script/ci/github-action/build_single.sh']
        cmd += [cfg['degree']]
        cmd += [cfg['major']]
        cmd += [cfg['thesis_type']]
        cmd += [cfg['period']]
        cmd += ['true' if cfg['blind'] else 'false']
        cmd += [cfg['grad_level']]
        cmd += [cfg['language']]
        run(cmd, capture_output=False)


if __name__ == '__main__':
    update()
