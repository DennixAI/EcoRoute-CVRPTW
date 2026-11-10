"""Execute the modeling notebook using this Python environment; never optimize routes."""
import argparse
import os
from pathlib import Path
import sys

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--strict', action='store_true', help='Fail if any required benchmark pair is missing')
    parser.add_argument('--data-root', type=Path, help='Override data/benchmarks/vrptw')
    parser.add_argument('--output', type=Path, default=Path('outputs/main.executed.ipynb'), help='Executed copy; source main.ipynb is preserved')
    args = parser.parse_args()
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
    notebook = nbformat.read(root/'main.ipynb', as_version=4)
    # Avoid accidentally using a global kernel with a different dependency set.
    manager = KernelManager(kernel_name='python3')
    manager.kernel_spec.argv = [sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}']
    print(f'Executing with {sys.executable}; strict={args.strict}; data={data}', flush=True)
    NotebookClient(notebook, km=manager, timeout=600,
                   resources={'metadata': {'path': str(root)}}).execute()
    output.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(notebook, output)
    print(f'Execution completed: {output}')

if __name__ == '__main__':
    main()
