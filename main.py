import os
import threading
import Levenshtein
matches = []
matches_lock = threading.Lock()


def build_path(start_path):
    current_path = start_path
    while True:
        try:
            subfolders = sorted([entry.name for entry in os.scandir(current_path) if entry.is_dir() and entry.name not in ['.', '..']], key=str.lower)
        except OSError as e:
            print(f"Error accessing {current_path}: {e}")
            return current_path  # Return current path if access fails

        print(f"Current path: {current_path}")
        if subfolders:
            print("Subfolders:")
            for i, folder in enumerate(subfolders, 1):
                print(f"{i}. {folder}")
            print("0. Confirm path")
            if current_path != start_path:
                print("-1. Go back to parent")
        else:
            print("No subfolders found.")

        choice = input("Enter number, folder name, or -1 to go back: ").strip()

        if choice == '0':
            return current_path
        elif choice == '-1':
            if current_path != start_path:
                current_path = os.path.dirname(current_path)
            else:
                print("Already at root directory.")
        elif choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(subfolders):
                selected_folder = subfolders[index]
                current_path = os.path.join(current_path, selected_folder)
            else:
                print("Invalid number.")
        else:
            matching_folders = [f for f in subfolders if f.lower() == choice.lower()]
            if matching_folders:
                selected_folder = matching_folders[0]
                current_path = os.path.join(current_path, selected_folder)
            else:
                print("No matching folder found.")

def check_word(string: str, target: str):
    """
    Сравнивает строки используя дистанцию Левенштейна, конвертирует разницу в проценты
    100 - идентично
    0 - абсолютно разные
    :param string: Имя файла/папки для сравнения с искомым именем
    :param target: Искомое имя
    """
    distance = Levenshtein.distance(string, target)
    similarity = 100 * (1 - (distance / max(len(string), len(target))))
    return similarity



def dirWalk(targetFile, content_chunk, rootDir):
    """
    С помощью os.walk проверить все файлы начиная с корневой директории
    :param targetFile: Искомое имя
    :param content_chunk: 5 (или меньше) папок которые будут обрабатываться одним потоком
    :param rootDir: Корневая директория
    :return: void, конец
    """
    is_exact = '.' in targetFile
    for folder in content_chunk:
        subroot = os.path.join(rootDir, folder)
        similarSubroot = check_word(folder, targetFile)
        if similarSubroot >= 70:
            with matches_lock:
                matches.append((subroot, similarSubroot, "folder"))
        try:
            for root, dirs, files in os.walk(subroot):
                for name in dirs:
                    name_lower = name.lower()
                    similar = check_word(name_lower, targetFile)
                    if similar >= 80:
                        path = os.path.join(root, name)
                        with matches_lock:
                            matches.append((path, similar, "folder"))

                for name in files:
                    name_lower = name.lower()
                    if is_exact:
                        if name_lower == targetFile:
                            path = os.path.join(root, name)
                            with matches_lock:
                                matches.append((path, 100, "file"))
                    else:
                        base_name = os.path.splitext(name_lower)[0]
                        similar = check_word(base_name, targetFile)
                        if similar >= 80:
                            path = os.path.join(root, name)
                            with matches_lock:
                                matches.append((path, similar, "file"))
        except (PermissionError, OSError) as e:
            print(f"Error accessing {subroot}: {e}")

    return


def main():
    rootDir = build_path(r"C:\\")
    targetFile = ''
    while targetFile=='':
        targetFile = input("Enter target file/folder name: ")
    targetFile = targetFile.lower()
    targetFile = targetFile.strip()



    if not os.path.exists(rootDir):
        print(f"Directory {rootDir} does not exist.")
        return

    contents = os.listdir(rootDir)
    if not contents:
        print(f"No directories found in {rootDir}.")
        return

    threads = []
    chunk_size = 5
    chunks = [contents[i:i + chunk_size] for i in range(0, len(contents), chunk_size)]

    for i, chunk in enumerate(chunks):
        t = threading.Thread(target=dirWalk, args=(targetFile, chunk, rootDir))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()
    if matches:
        # Separate files and folders
        files = [m for m in matches if m[2] == "file"]
        folders = [m for m in matches if m[2] == "folder"]

        # Sort both groups by accuracy (descending) and path length (ascending)
        files.sort(key=lambda x: (-x[1], len(x[0])))
        folders.sort(key=lambda x: (-x[1], len(x[0])))

        # Combine them: files first, then folders
        sorted_matches = files + folders

        # Display
        for path, accuracy, type_label in sorted_matches:
            print(f"Found {type_label}: {path} (Accuracy: {accuracy:.2f}%)")
    else:
        print(f"No file or folder named '{targetFile}' found.")

if __name__ == "__main__":
    main()