from pathlib import Path
import mkdocs_gen_files

nav = mkdocs_gen_files.Nav()

for path in sorted(Path("parsers").rglob("*.py")):
    print("===================================")
    module_path = path.with_suffix("")
    doc_path = path.with_suffix(".md")
    full_doc_path = Path("reference", doc_path)

    parts = tuple(module_path.parts)

    print("path:", path)
    print("module_path:", module_path)
    print("doc_path:", doc_path)
    print("full_doc_path:", full_doc_path)
    print('parts:', parts)

    if parts[-1] == "__init__":
        print("modify init")
        parts = parts[:-1]
        doc_path = doc_path.with_name("index.md")
        full_doc_path = full_doc_path.with_name("index.md")
        print("doc_path:", doc_path)
        print("full_doc_path:", full_doc_path)
        print('parts:', parts)
    elif parts[-1] == "__main__":
        continue

    nav[parts] = doc_path.as_posix()

    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        print("writing")
        ident = ".".join(parts)
        fd.write(f"::: {ident}")

    mkdocs_gen_files.set_edit_path(full_doc_path, path)

with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
