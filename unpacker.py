import os
import tarfile
import zipfile
import gzip
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any

StrPath = Path | str


def is_compressed(file_path: StrPath) -> bool:
    return any(str(file_path).endswith(ext) for ext in ('.tar', '.zip', '.gz'))


def list_contents(file_path: StrPath) -> List[str]:
    """
    Lists the contents of a compressed file based on its extension.
    Returns a list of file paths/names contained in the archive.

    Args:
        file_path: Path to the compressed file

    Returns:
        List of file paths/names in the archive

    Raises:
        ValueError: If file extension is not supported
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == '.tar' or str(file_path).endswith('.tar.gz'):
        return list_tar_contents(file_path)
    elif ext == '.zip':
        return list_zip_contents(file_path)
    elif ext == '.gz':
        return list_gz_contents(file_path)

    raise ValueError(f"Unsupported file extension: {ext}")


def list_tar_contents(file_path: StrPath) -> List[str]:
    """
    Lists all files and directories in a .tar or .tar.gz file.

    Args:
        file_path: Path to the tar file

    Returns:
        List of file/directory names in the tar archive
    """
    ext = os.path.splitext(file_path)[1].lower()
    mode = 'r' if ext == '.tar' else 'r:gz'

    with tarfile.open(file_path, mode) as tar:
        return tar.getnames()


def list_zip_contents(file_path: StrPath) -> List[str]:
    """
    Lists all files and directories in a .zip file.

    Args:
        file_path: Path to the zip file

    Returns:
        List of file/directory names in the zip archive
    """
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        return zip_ref.namelist()


def list_gz_contents(file_path: StrPath) -> List[str]:
    """
    Lists the content of a .gz file.
    Since .gz files typically contain a single compressed file,
    this returns a list with the name of the decompressed file.

    Args:
        file_path: Path to the .gz file

    Returns:
        List containing the name of the decompressed file
    """
    file_name = os.path.splitext(os.path.basename(file_path))[0]
    return [file_name]


def get_detailed_contents(file_path: StrPath) -> List[Dict[str, Any]]:
    """
    Gets detailed information about the contents of a compressed file.

    Args:
        file_path: Path to the compressed file

    Returns:
        List of dictionaries with detailed file information

    Raises:
        ValueError: If file extension is not supported
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == '.tar' or str(file_path).endswith('.tar.gz'):
        return get_tar_details(file_path)
    elif ext == '.zip':
        return get_zip_details(file_path)
    elif ext == '.gz':
        return get_gz_details(file_path)

    raise ValueError(f"Unsupported file extension: {ext}")


def get_tar_details(file_path: StrPath) -> List[Dict[str, Any]]:
    """
    Gets detailed information about files in a tar archive.

    Args:
        file_path: Path to the tar file

    Returns:
        List of dictionaries with file details (name, size, mtime, is_directory)
    """
    ext = os.path.splitext(file_path)[1].lower()
    mode = 'r' if ext == '.tar' else 'r:gz'

    details: List[Dict[str, Any]] = []
    with tarfile.open(file_path, mode) as tar:
        for member in tar.getmembers():
            details.append({
                'name': member.name,
                'size': member.size,
                'mtime': member.mtime,
                'is_directory': member.isdir(),
                'is_file': member.isfile(),
                'mode': member.mode
            })
    return details


def get_zip_details(file_path: StrPath) -> List[Dict[str, Any]]:
    """
    Gets detailed information about files in a zip archive.

    Args:
        file_path: Path to the zip file

    Returns:
        List of dictionaries with file details (name, size, compress_size, date_time, is_directory)
    """
    details: List[Dict[str, Any]] = []
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        for info in zip_ref.infolist():
            details.append({
                'name': info.filename,
                'size': info.file_size,
                'compress_size': info.compress_size,
                'date_time': info.date_time,
                'is_directory': info.is_dir(),
                'compression': info.compress_type
            })
    return details


def get_gz_details(file_path: StrPath) -> List[Dict[str, Any]]:
    """
    Gets information about a .gz file.

    Args:
        file_path: Path to the .gz file

    Returns:
        List with a single dictionary containing file information
    """
    file_name = os.path.splitext(os.path.basename(file_path))[0]
    file_stats = os.stat(file_path)

    return [{
        'name': file_name,
        'compressed_size': file_stats.st_size,
        'mtime': file_stats.st_mtime,
        'is_directory': False
    }]


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

        preserve_structure = FlagArg('--ps', '--preserve-structure', help='Preserve folder structure inside the compressed file')

        list = FlagArg('-l', '--list', help='List contents of the compressed file without extracting')

        def _post_validate(self):
            print(f'{self.list.value=}, {self.output_dir.value=}, {self.preserve_structure.value=}')
            print(f'{UnpackerArgs.list.value=}, {UnpackerArgs.output_dir.value=}, {UnpackerArgs.preserve_structure.value=}')
            if self.list.value:
                assert not self.output_dir.value and not self.preserve_structure.value, \
                    "Cannot use --list with --output-dir or --preserve-structure"

    args = UnpackerArgs()
    for path in args.file_paths.values:
        if not args.list.value:
            extract_all_files(path, args.output_dir.value,
                              args.preserve_structure.value)
        else:
            contents = list_contents(path)
            print(f"Contents of {path}:")
            for item in contents:
                print(f" - {item}")
