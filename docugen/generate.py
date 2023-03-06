"""Generate tensorflow.org style API Reference docs for a Python module."""

import os
import pathlib
import shutil
import tempfile
import re
from markdownify import MarkdownConverter

from typing import Any, Dict, List, Optional, Sequence, Tuple, Type, Union

from docugen import doc_generator_visitor
from docugen import parser
from docugen import pretty_docs
from docugen import public_api
from docugen import traverse

EXCLUDED = set(["__init__.py", "OWNERS", "README.txt"])

class DocusaurusConverter(MarkdownConverter):
    def __init__(self):
        super().__init__()

    def multiple_replace(self, dict, text):
        """
        Checks characters defined in dictionary and replaces them with desired output.
        Args:
            text (str): A string that contains markdown content.
            dict (dict): A dictionary with key-value pairs {current_string : desired_string}
        """
        # Create a regular expression  from the dictionary keys
        regex = re.compile("(%s)" % "|".join(map(re.escape, dict.keys())))

        # For each match, look-up corresponding value in dictionary
        return regex.sub(lambda mo: dict[mo.string[mo.start():mo.end()]], text)



class DocGenerator:
    """Main entry point for generating docs."""

    def __init__(
        self,
        root_title: str,
        py_modules: Sequence[Tuple[str, Any]],
        base_dir: Optional[Sequence[Union[str, pathlib.Path]]] = None,
        code_url_prefix: Sequence[str] = (),
        private_map: Optional[Dict[str, str]] = None,
        visitor_cls: Type[
            doc_generator_visitor.DocGeneratorVisitor
        ] = doc_generator_visitor.DocGeneratorVisitor,
        callbacks: Optional[List[public_api.ApiFilter]] = None,
    ):
        """Creates a doc-generator.

        Args:
          root_title: A string. The main title for the project. Like "TensorFlow"
          py_modules: The python module to document.
          base_dir: String or tuple of strings. Directories that "Defined in" links
            are generated relative to. Modules outside one of these directories are
            not documented. No `base_dir` should be inside another.
          code_url_prefix: String or tuple of strings. The prefix to add to "Defined
            in" paths. These are zipped with `base-dir`, to set the `defined_in`
            path for each file. The defined in link for `{base_dir}/path/to/file` is
            set to `{code_url_prefix}/path/to/file`.
          private_map: A {"module.path.to.object": ["names"]} dictionary. Specific
            aliases that should not be shown in the resulting docs.
          visitor_cls: An option to override the default visitor class
            `doc_generator_visitor.DocGeneratorVisitor`.
          callbacks: Additional callbacks passed to `traverse`. Executed between the
            `PublicApiFilter` and the accumulator (`DocGeneratorVisitor`). The
            primary use case for these is to filter the list of children (see:
              `public_api.ApiFilter` for the required signature)
        """
        self._root_title = root_title
        self._py_modules = py_modules
        self._short_name = py_modules[0][0]
        self._py_module = py_modules[0][1]

        if base_dir is None:
            # Determine the base_dir for the module
            base_dir = public_api.get_module_base_dirs(self._py_module)
        else:
            if isinstance(base_dir, (str, pathlib.Path)):
                base_dir = (base_dir,)
            base_dir = tuple(pathlib.Path(d) for d in base_dir)
        self._base_dir = base_dir

        if not self._base_dir:
            raise ValueError("`base_dir` cannot be empty")

        if isinstance(code_url_prefix, str):
            code_url_prefix = (code_url_prefix,)
        self._code_url_prefix = tuple(code_url_prefix)
        if not self._code_url_prefix:
            raise ValueError("`code_url_prefix` cannot be empty")

        if len(self._code_url_prefix) != len(base_dir):
            raise ValueError(
                "The `base_dir` list should have the same number of "
                "elements as the `code_url_prefix` list (they get "
                "zipped together)."
            )

        self._private_map = private_map or {}
        self._visitor_cls = visitor_cls
        if callbacks is None:
            callbacks = []
        self._callbacks = callbacks

    def make_reference_resolver(self, visitor):
        return parser.ReferenceResolver.from_visitor(
            visitor, py_module_names=[self._short_name]
        )

    def make_parser_config(self, visitor, reference_resolver):
        return parser.ParserConfig(
            reference_resolver=reference_resolver,
            duplicates=visitor.duplicates,
            duplicate_of=visitor.duplicate_of,
            tree=visitor.tree,
            index=visitor.index,
            reverse_index=visitor.reverse_index,
            base_dir=self._base_dir,
            code_url_prefix=self._code_url_prefix,
        )

    def run_extraction(self):
        """Walks the module contents, returns an index of all visited objects.

        The return value is an instance of `self._visitor_cls`, usually:
        `doc_generator_visitor.DocGeneratorVisitor`

        Returns:
        """
        return self.extract(
            py_modules=self._py_modules,
            base_dir=self._base_dir,
            private_map=self._private_map,
            visitor_cls=self._visitor_cls,
            callbacks=self._callbacks,
        )

    def build(self, output_dir):
        """Build all the docs.

        This produces python api docs:
          * generated from `py_module`.
          * written to '{output_dir}/api_docs/python/'

        Args:
          output_dir: Where to write the resulting docs.
        """
        workdir = pathlib.Path(tempfile.mkdtemp())

        # Extract the python api from the _py_modules
        visitor = self.run_extraction()
        reference_resolver = self.make_reference_resolver(visitor)
        # Write the api docs.
        parser_config = self.make_parser_config(visitor, reference_resolver)
        work_py_dir = workdir / "api_docs/python"
        self.write_docs(
            output_dir=str(work_py_dir),
            parser_config=parser_config,
            root_title=self._root_title,
            root_module_name=self._short_name.replace(".", "/"),
        )

        try:
            os.makedirs(output_dir)
        except OSError as e:
            if e.strerror != "File exists":
                raise

        # Typical results are something like:
        #
        # out_dir/
        #    {short_name}/
        #    index.md
        #    {short_name}.md
        #
        # Copy the top level files to the `{output_dir}/`, delete and replace the
        # `{output_dir}/{short_name}/` directory.

        glob_pattern = "*"

        for work_path in work_py_dir.glob(glob_pattern):
            out_path = pathlib.Path(output_dir) / work_path.name
            out_path.parent.mkdir(exist_ok=True, parents=True)

            if work_path.is_file():
                shutil.copy2(work_path, out_path)
            elif work_path.is_dir():
                shutil.rmtree(out_path, ignore_errors=True)
                shutil.copytree(work_path, out_path)

    def write_docs(
        self,
        output_dir: Union[str, pathlib.Path],
        parser_config: parser.ParserConfig,
        root_module_name: str,
        root_title: str = "wandb",
    ):
        """Write previously extracted docs to disk.

        Write a docs page for each symbol included in the indices of parser_config to
        a tree of docs at `output_dir`.

        Symbols with multiple aliases will have only one page written about
        them, which is referenced for all aliases.

        Args:
          output_dir: Directory to write documentation markdown files to. Will be
            created if it doesn't exist.
          parser_config: A `parser.ParserConfig` object, containing all the necessary
            indices.
          root_module_name: (str) the name of the root module (`tf` for tensorflow).
          root_title: The title name for the root level index.md.

        Raises:
          ValueError: if `output_dir` is not an absolute path
        """
        output_dir = pathlib.Path(output_dir)

        # Make output_dir.
        if not output_dir.is_absolute():
            raise ValueError(
                "'output_dir' must be an absolute path.\n"
                f"    output_dir='{output_dir}'"
            )
        output_dir.mkdir(parents=True, exist_ok=True)

        # Parse and write Markdown pages, resolving cross-links (`tf.symbol`).
        for full_name in sorted(parser_config.index.keys(), key=lambda k: k.lower()):
            py_object = parser_config.index[full_name]

            if full_name in parser_config.duplicate_of:
                continue

            # Methods constants are only documented only as part of their parent's page.
            if parser_config.reference_resolver.is_fragment(full_name):
                continue

            # Remove the extension from the path.
            docpath, _ = os.path.splitext(parser.documentation_path(full_name))

            # Generate docs for `py_object`, resolving references.
            try:
                page_info = parser.docs_for_object(
                    full_name,
                    py_object,
                    parser_config,
                )
            except:  # noqa
                raise ValueError(f"Failed to generate docs for symbol: `{full_name}`")

            path = output_dir / parser.documentation_path(full_name)

            content = []
            content.append(pretty_docs.build_md_page(page_info))

            # Clean up markdown and remove characters that break Docusuarus
            dictionary = {
                "<" : "",
                "->" : "->",
                ">" : "",
                "\*" : "*"
                "\*\*" : "**"
                } 

            # Create custom DocusaurusConverter Class that inherits from MarkdownConverter
            docu_converter = DocusaurusConverter()
            docu_converter.DefaultOptions.escape_underscores = False

            # Convert text to markdown
            markdown_content = docu_converter.convert("\n".join(content))
            
            # Remove undesirable characters and/or clean artifacts from markdown convert.
            text = docu_converter.multiple_replace(dictionary, markdown_content)
            
            try:
                path.parent.mkdir(exist_ok=True, parents=True)
                path.write_text(text, encoding="utf-8")
            except OSError:
                raise OSError(
                    "Cannot write documentation for " f"{full_name} to {path.parent}"
                )

            duplicates = parser_config.duplicates.get(full_name, [])
            if not duplicates:
                continue

            duplicates = [item for item in duplicates if item != full_name]

    def extract(
        self,
        py_modules,
        base_dir,
        private_map,
        visitor_cls=doc_generator_visitor.DocGeneratorVisitor,
        callbacks=None,
    ):
        """Walks the module contents, returns an index of all visited objects.

        The return value is an instance of `self._visitor_cls`, usually:
        `doc_generator_visitor.DocGeneratorVisitor`

        Args:
          py_modules: A list containing a single (short_name, module_object) pair.
            like `[('tf',tf)]`.
          base_dir: The package root directory. Nothing defined outside of this
            directory is documented.
          private_map: A {'path':["name"]} dictionary listing particular object
            locations that should be ignored in the doc generator.
          visitor_cls: A class, typically a subclass of
            `doc_generator_visitor.DocGeneratorVisitor` that acumulates the indexes of
            objects to document.
          callbacks: Additional callbacks passed to `traverse`. Executed between the
            `PublicApiFilter` and the accumulator (`DocGeneratorVisitor`). The
            primary use case for these is to filter the list of children (see:
              `public_api.local_definitions_filter`)

        Returns:
          The accumulator (`DocGeneratorVisitor`)
        """
        if callbacks is None:
            callbacks = []

        if len(py_modules) != 1:
            raise ValueError("only pass one [('name',module)] pair in py_modules")
        short_name, py_module = py_modules[0]

        api_filter = public_api.PublicAPIFilter(
            base_dir=base_dir, private_map=private_map
        )

        accumulator = visitor_cls()

        # The objects found during traversal, and their children are passed to each
        # of these visitors in sequence. Each visitor returns the list of children
        # to be passed to the next visitor.
        visitors = [api_filter, public_api.ignore_typing] + callbacks + [accumulator]

        traverse.traverse(py_module, visitors, short_name)

        return accumulator
