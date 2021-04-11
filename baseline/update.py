import click
import json

def update_single(ctx, major, degree, doc_type, period, blind, grad_level):
    # Check args
    assert major in ['general', 'cs', 'isee', 'math', 'physics']
    assert degree in ['undergraduate', 'graduate']
    assert doc_type ['thesis', 'design']
    assert period in ['proposal', 'final']
    assert grad_level in ['master', 'doctor']

    # Output filename
    filename = f'zjuthesis-{degree}-{grad_level}-{grad_level}-{major}-{doc_type}-{period}'
    if blind:
        filename += f'-blind'
    filename += f'.pdf'



@click.group()
@click.pass_context
def update(ctx):
    ctx.ensure_object(dict)
    with open('baseline.json', 'r') as f:
        ctx.obj['baseline'] = json.load(f)


@update.command()
@click.option('-m', '--major', required=True)
@click.option('-d', '--degree', required=True)
@click.option('-t', '--doc_type', required=True)
@click.option('-p', '--period', required=True)
@click.option('-b', '--blind', is_flag=True)
@click.option('-l', '--grad_level', default='master')
@click.pass_context
def single(ctx, major, degree, doc_type, period, blind, grad_level):
    '''Update single baseline pdf file'''
    update_single(ctx, major, degree, doc_type, period, blind, grad_level)

@update.command()
@click.pass_context
def preset(ctx):
    '''Update preset baseline pdf files'''
    pass


if __name__ == '__main__':
    update()