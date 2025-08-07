def read_instructions(file_name: str) -> str:
    """Read and return the contents of a file.

    Args:
        file_path (str): The path to the file to be read.

    Returns:
        str: The complete contents of the file as a string.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        IOError: If there are issues reading the file.
    """
    with open(f"src/{file_name}", "r") as file:
        return file.read()