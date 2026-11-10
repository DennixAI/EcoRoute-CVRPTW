"""Execute the modeling notebook using this Python environment; never optimize routes.

With --publish (requires --strict), a successful run also stores its outputs (figures,
tables, printed results) in main.ipynb itself, so they are visible without re-running,
for example on GitHub, and refreshes the README figures in docs/figures/.
"""
import argparse
import os
from pathlib import Path
import sys

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--strict', action='store_true', help='Fail if any required benchmark pair is missing')
    parser.add_argument('--data-root', type=Path, help='Override data/benchmarks/vrptw')
    parser.add_argument('--output', type=Path, default=Path('outputs/main.executed.ipynb'), help='Executed copy; source main.ipynb is preserved')
    parser.add_argument('--publish', action='store_true',
                        help='After a successful strict run, save the outputs into main.ipynb and refresh docs/figures/')
    args = parser.parse_args()
    if args.publish and not args.strict:
        parser.error('--publish requires --strict (published outputs must come from the complete collection)')
    import nbformat
    from nbclient import NotebookClient
    from jupyter_client import KernelManager

    root = Path(__file__).resolve().parent.parent
    data = (args.data_root.resolve() if args.data_root else root/'data'/'benchmarks'/'vrptw')
    output = args.output.resolve()
    if output == root/'main.ipynb':
        parser.error('Choose a separate executed output, not main.ipynb')
    os.environ['ECOROUTE_PROJECT_ROOT'] = str(root)
    os.environ['ECOROUTE_DATA_ROOT'] = str(data)
    os.environ['ECOROUTE_STRICT_DATA'] = '1' if args.strict else '0'
    os.environ['ECOROUTE_EXPORT_FIGURES'] = '1' if args.publish else os.environ.get('ECOROUTE_EXPORT_FIGURES', '0')
    notebook = nbformat.read(root/'main.ipynb', as_version=4)
    sources = [cell.source for cell in notebook.cells]
    # Avoid accidentally using a global kernel with a different dependency set.
    manager = KernelManager(kernel_name='python3')
    manager.kernel_spec.argv = [sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}']
    print(f'Executing with {sys.executable}; strict={args.strict}; data={data}', flush=True)
    NotebookClient(notebook, km=manager, timeout=600,
                   resources={'metadata': {'path': str(root)}}).execute()
    output.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(notebook, output)
    print(f'Execution completed: {output}')
    if args.publish:
        if [cell.source for cell in nbformat.read(root/'main.ipynb', as_version=4).cells] != sources:
            sys.exit('main.ipynb was edited during the run; outputs NOT stored (run again)')
        publish(notebook, root)
        nbformat.write(notebook, root/'main.ipynb')
        print(f'Outputs stored in {root/"main.ipynb"}; README figures refreshed in {root/"docs"/"figures"}')


def publish(notebook, root):
    """Drop per-cell timing metadata and replace local absolute paths in text outputs."""
    replacements = [(str(root), '<repo>'), (str(Path.home()), '~')]

    def clean(text):
        for old, new in replacements:
            text = text.replace(old, new)
        return text

    for cell in notebook.cells:
        cell.metadata.pop('execution', None)
        for out in cell.get('outputs', []):
            if 'text' in out:
                out['text'] = clean(out['text'])
            for key in ('text/plain', 'text/markdown', 'text/html'):
                if key in out.get('data', {}):
                    value = out['data'][key]
                    out['data'][key] = clean(value) if isinstance(value, str) else [clean(v) for v in value]

if __name__ == '__main__':
    main()
