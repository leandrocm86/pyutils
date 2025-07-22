import os
import tarfile
import zipfile
import gzip
import shutil
from pathlib import Path
from typing import Optional

StrPath = Path | str


def is_compressed(file_path: StrPath) -> bool:
    return any(str(file_path).endswith(ext) for ext in ('.tar', 'zip', '.gz'))


def extract_all_files(file_path: StrPath, output_dir: Optional[StrPath] = None,
                      preserve_structure: bool = True) -> list[str]:
    """
    Function that checks the given compressed file's extension and extracts it with the appropriate module.
    It accepts .zip, .tar.gz and .gz files.
    By default, the files are extracted into the same directory of the compressed file (that can be changed with output_dir).
    By default, the folder structure inside the compressed file is preserved (that can be changed with preserve_structure).
    Returns a list with the extracted files' paths.
    """

    ext = os.path.splitext(file_path)[1].lower()
    out = str(output_dir) if output_dir else 'the same folder'

    print(f"Extracting {file_path} to {out}")

    if ext == '.tar' or ext == '.tar.gz':
        return extract_tar_file(file_path, output_dir, preserve_structure)
    elif ext == '.zip':
        return extract_zip_file(file_path, output_dir, preserve_structure)
    elif ext == '.gz':
        return [extract_gz_file(file_path, output_dir)]

    raise ValueError(f"Unsupported file extension: {ext}")


def extract_tar_file(file_path: StrPath, output_dir: Optional[StrPath] = None,
                     preserve_structure: bool = True) -> list[str]:
    """
    Extracts all files from a .tar or .tar.gz file into a specified output directory.
    By default, the files are extracted into the same directory of the compressed file (that can be changed with output_dir).
    By default, the folder structure inside the compressed file is preserved.
    Returns a list with the extracted files' paths.
    """
    if output_dir is None:
        output_dir = os.path.dirname(file_path)
    ext = os.path.splitext(file_path)[1].lower()
    assert ext == '.tar.gz' or ext == '.tar'
    mode = 'r' if ext == '.tar' else 'r:gz'

    extracted_paths: list[str] = []
    with tarfile.open(file_path, mode) as tar:
        if preserve_structure:
            tar.extractall(path=output_dir)
        else:
            for member in tar.getmembers():
                if member.isfile():
                    tar.extract(member, path=output_dir)
        for member in tar.getmembers():
            if member.isfile():
                extracted_paths.append(os.path.join(output_dir, member.name))

    return extracted_paths


def extract_zip_file(file_path: StrPath, output_dir: Optional[StrPath] = None,
                     preserve_structure: bool = True) -> list[str]:
    """
    Extracts all files from a .zip file into a specified output directory.
    By default, the files are extracted into the same directory of the compressed file.
    By default, the folder structure inside the compressed file is preserved.
    Returns a list with the extracted files' paths.
    """
    assert str(file_path).lower().endswith('.zip')
    if output_dir is None:
        output_dir = os.path.dirname(file_path)

    extracted_paths: list[str] = []
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        if preserve_structure:
            zip_ref.extractall(path=output_dir)
        else:
            for file in zip_ref.namelist():
                if not file.endswith('/'):  # Exclude directories
                    zip_ref.extract(file, path=output_dir)
        for file in zip_ref.namelist():
            if not file.endswith('/'):  # Exclude directories
                extracted_paths.append(os.path.join(output_dir, file))

    return extracted_paths


def extract_gz_file(file_path: StrPath, output_dir: Optional[StrPath] = None) -> str:
    """
    Extracts a .gz file into a specified output directory.
    If no output directory is specified, the files are extracted into the same directory of the compressed file.
    Returns the path of the decompressed file.
    """
    file_name, ext = os.path.splitext(file_path)
    assert ext.lower() == '.gz'
    if output_dir is None:
        output_dir = os.path.dirname(file_path)
    with gzip.open(file_path, 'rb') as f_in:
        decompressed_file_path = os.path.join(output_dir, file_name)
        with open(decompressed_file_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)  # type: ignore
        return decompressed_file_path


if __name__ == "__main__":
    from mods.cliparse import CliParser, OptArg, VarArgs, FlagArg

    class UnpackerArgs(CliParser):
        file_paths = VarArgs('file_paths', nargs='+', help='Path to the compressed file to unpack', type=Path,
                             validation=lambda p: p.exists() and is_compressed(p))

        output_dir = OptArg('-o', '--output-dir', type=Path, validation=lambda p: p.is_dir() and os.access(p, os.W_OK),
                            help='Directory to extract files to (default: same as file path)')

        preserve_structure = FlagArg(
            '--ps', '--preserve-structure', help='Preserve folder structure inside the compressed file')

    args = UnpackerArgs()
    for path in args.file_paths.values:
        extract_all_files(path, args.output_dir.value, args.preserve_structure.value)
