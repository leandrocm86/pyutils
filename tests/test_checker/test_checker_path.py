import pytest
from pathlib import Path
from typeguard import TypeCheckError

from mods.checker import pathok, InvalidContractError

# Test paths that must be created previously.
TEST_BASEPATH = Path(__file__).parent / 'path_examples'
WRX_DIR = TEST_BASEPATH / 'wrx_dir'
WRX_DIR_WRX_FILE = WRX_DIR / 'wrx_file'
WRX_DIR_ROOT_FILE = WRX_DIR / 'wrx_root_file'
WRX_DIR_RX_FILE = WRX_DIR / 'rx_file'
WRX_DIR_RX_SUBDIR = WRX_DIR / 'rx_subdir'
WRX_DIR_RX_SUBDIR_R_FILE = WRX_DIR_RX_SUBDIR / 'r_file'
WR_DIR = TEST_BASEPATH / 'wr_dir'  # May have to be added in pytest.ini to be ignored
WR_DIR_WRX_FILE = WR_DIR / 'wrx_file'

# Test paths that should not exist
WRX_DIR_NON_EXISTENT = WRX_DIR / 'non_existent_dir'
WRX_DIR_NON_EXISTENT_FILE = WRX_DIR / 'non_existent_file.txt'


class TestPathOk:
    """Test suite for the pathok function"""

    def test_type_checking(self):
        """Test that the function correctly validates the input type"""

        with pytest.raises(TypeCheckError):
            pathok('/nfs/scripts/')  # type: ignore

    def test_exists_check(self):
        """Test checking if a path exists or not"""
        # Successful case - file exists
        pathok(WRX_DIR_WRX_FILE, exists=True)
        pathok(WRX_DIR_ROOT_FILE, exists=True)

        # Successful case - file doesn't exist as expected
        pathok(WRX_DIR_NON_EXISTENT_FILE, exists=False)

        # Error case - expecting a file to exist when it doesn't
        with pytest.raises(InvalidContractError, match=f"Path {WRX_DIR_NON_EXISTENT_FILE} doesn't exist"):
            pathok(WRX_DIR_NON_EXISTENT_FILE, exists=True)

        # Error case - expecting a file to not exist when it does
        with pytest.raises(InvalidContractError, match=f"Path {WRX_DIR_WRX_FILE} exists"):
            pathok(WRX_DIR_WRX_FILE, exists=False)

    def test_is_file(self):
        """Test that a valid existing file passes all checks"""
        # Successful case
        pathok(WRX_DIR_WRX_FILE, is_dir=False)
        pathok(WRX_DIR_ROOT_FILE, is_dir=False)

        # Error case - file does not exist
        with pytest.raises(InvalidContractError, match="Impossible to check if path"):
            pathok(WRX_DIR_NON_EXISTENT_FILE, is_dir=False)

        # Error case - expecting a directory to be a file
        with pytest.raises(InvalidContractError, match="Invalid path: expected file, got directory"):
            pathok(WRX_DIR, is_dir=False)

    def test_is_directory(self):
        """Test that a valid existing directory passes all checks"""
        # Successful case
        pathok(WRX_DIR, is_dir=True)
        pathok(WRX_DIR_RX_SUBDIR, is_dir=True)

        # Error case - directory does not exist
        with pytest.raises(InvalidContractError, match="Impossible to check if path"):
            pathok(TEST_BASEPATH / 'non_existent', is_dir=True)

        # Error case - expecting a file to be a directory
        with pytest.raises(InvalidContractError, match="Invalid path: expected directory, got file"):
            pathok(WRX_DIR_WRX_FILE, is_dir=True)

    def test_file_permissions_read(self):
        """Test checking file read permission"""
        # Successful case - readable file
        pathok(WRX_DIR_RX_FILE, can_read_if_exists=True)
        pathok(WRX_DIR_RX_SUBDIR_R_FILE, can_read_if_exists=True)

        # Asserts root file is not readable
        pathok(WRX_DIR_ROOT_FILE, can_read_if_exists=False)

        # Error case - expecting file to be readable when it's not
        with pytest.raises(InvalidContractError, match="Invalid read path permissions"):
            pathok(WRX_DIR_ROOT_FILE, can_read_if_exists=True)

    def test_file_permissions_write(self):
        """Test checking file write permission"""
        # Successful case - writable file
        pathok(WRX_DIR_WRX_FILE, can_modify_if_exists=True)

        # Asserts read-only file is not writable
        pathok(WRX_DIR_RX_FILE, can_modify_if_exists=False)

        # Error case - expecting file to be writable when it's not
        with pytest.raises(InvalidContractError, match="Invalid write path permissions"):
            pathok(WRX_DIR_RX_FILE, can_modify_if_exists=True)

    def test_file_permissions_execute(self):
        """Test checking file execute permission"""
        # Successful case - executable file
        pathok(WRX_DIR_WRX_FILE, can_execute_if_exists=True)
        pathok(WRX_DIR_RX_FILE, can_execute_if_exists=True)

        # Error case - expecting file to be executable when it's not
        with pytest.raises(InvalidContractError, match="Invalid execute path permissions"):
            pathok(WRX_DIR_RX_SUBDIR_R_FILE, can_execute_if_exists=True)

    def test_directory_permissions(self):
        """Test checking directory permissions"""
        # Successful case - directory with all permissions
        pathok(WRX_DIR, can_read_if_exists=True,
               can_modify_if_exists=True, can_execute_if_exists=True)

        # Successful case - directory with readonly and execute permissions
        pathok(WRX_DIR_RX_SUBDIR, can_read_if_exists=True,
               can_modify_if_exists=False, can_execute_if_exists=True)

        # Error case - expecting directory to be writable when it's not
        with pytest.raises(InvalidContractError, match="Invalid write path permissions"):
            pathok(WRX_DIR_RX_SUBDIR, can_modify_if_exists=True)

    def test_can_create_if_not_exists(self):
        """Test checking if we can create a file if it doesn't exist"""

        # Successful case - we can create file in writable directory
        pathok(WRX_DIR_NON_EXISTENT, exists=False, can_create_if_not_exists=True)

        # Successful case - we can't create file in read-only directory
        pathok(WRX_DIR_RX_SUBDIR / 'new_file.txt', exists=False, can_create_if_not_exists=False)

        # Successful case - already existing file (must not raise any error)
        pathok(WRX_DIR_WRX_FILE, can_create_if_not_exists=False)
        pathok(WRX_DIR_WRX_FILE, can_create_if_not_exists=True)

        # Error case - can't create file in read-only directory
        non_existent_file_in_rx_dir = WRX_DIR_RX_SUBDIR / 'new_file.txt'
        with pytest.raises(InvalidContractError, match="Invalid write path permissions for parent"):
            pathok(non_existent_file_in_rx_dir, exists=False, can_create_if_not_exists=True)

        # Error case - parent directory doesn't exist
        deep_non_existent = WRX_DIR_NON_EXISTENT / "new_file.txt"
        with pytest.raises(InvalidContractError, match="Parent .* doesn't even exist"):
            pathok(deep_non_existent, exists=False, can_create_if_not_exists=True)

    def test_match(self):
        """Test checking if a path matches a pattern"""
        # Successful case - path matches pattern
        pathok(WRX_DIR_WRX_FILE, match="*_file")

        # Error case - path doesn't match pattern
        with pytest.raises(InvalidContractError, match="Invalid path: expected match"):
            pathok(WRX_DIR_WRX_FILE, match="*.jpg")

    def test_full_match(self):
        """Test checking if a path fully matches a pattern"""

        # Successful case - path fully matches pattern
        pathok(Path('/grandparent/parent/dir/file.txt'), full_match='/*/*/*/*.txt')

        # Error case - path doesn't fully match pattern (subdirs are not included in '*')
        with pytest.raises(InvalidContractError, match="Invalid path: expected full match"):
            pathok(WRX_DIR_WRX_FILE, full_match="*wrx_file")

    def test_parent_traverse_errors(self):
        """Test checking parent directory traverse permissions"""

        with pytest.raises(InvalidContractError, match="parent folders seem to miss execute permission"):
            pathok(WR_DIR_WRX_FILE, exists=True)

        with pytest.raises(InvalidContractError, match="parent folders seem to miss execute permission"):
            pathok(WR_DIR_WRX_FILE, is_dir=False)

        with pytest.raises(InvalidContractError, match="parent folders seem to miss execute permission"):
            pathok(WR_DIR_WRX_FILE, can_read_if_exists=True)

        with pytest.raises(InvalidContractError, match="parent folders seem to miss execute permission"):
            pathok(WR_DIR / 'new_file', can_create_if_not_exists=True)

        # match doesn't raise error, because it does not actually access the path, only its URL.
        pathok(WR_DIR_WRX_FILE, match="*_file")

    def test_multiple_conditions(self):
        """Test checking multiple conditions at once"""
        # Successful case - multiple conditions pass
        pathok(WRX_DIR_WRX_FILE,
               exists=True,
               is_dir=False,
               can_read_if_exists=True,
               can_modify_if_exists=True,
               can_execute_if_exists=True)

        # Error case - one condition fails among many
        with pytest.raises(InvalidContractError, match="Invalid write path permissions"):
            pathok(WRX_DIR_RX_FILE,
                   exists=True,
                   is_dir=False,
                   can_read_if_exists=True,
                   can_modify_if_exists=True,  # This should fail
                   can_execute_if_exists=False)
