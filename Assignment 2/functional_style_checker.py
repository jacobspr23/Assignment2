import ast
import re
import sys
import os

def read_file(filepath):
    """Read the given file and return its lines."""
    with open(filepath, 'r') as file:
        lines = file.readlines()
    return lines

def parse_file_structure(filepath):
    """Parse the Python file and return a dictionary with structure info."""
    lines = read_file(filepath)
    lines_of_code = len(lines)

    # Parse AST
    with open(filepath, 'r') as file:
        tree = ast.parse(file.read(), filename=filepath)

    # Assign parent nodes for traversal
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            child.parent = node
    
    imports = []
    classes = []
    functions = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module if node.module else ""
            for alias in node.names:
                imports.append(f"{module}.{alias.name}")
        elif isinstance(node, ast.ClassDef):
            # Extract class info
            class_info = {
                'name': node.name,
                'docstring': ast.get_docstring(node),
                'methods': []
            }
            for class_node in node.body:
                if isinstance(class_node, ast.FunctionDef):
                    method_info = {
                        'name': class_node.name,
                        'docstring': ast.get_docstring(class_node),
                        'args': [{'name': arg.arg, 'annotation': annotation_to_string(arg.annotation)} for arg in class_node.args.args],
                        'returns': annotation_to_string(class_node.returns)
                    }
                    class_info['methods'].append(method_info)
            classes.append(class_info)
        elif isinstance(node, ast.FunctionDef):
            # If not inside a class
            if not isinstance(getattr(node, 'parent', None), ast.ClassDef):
                function_info = {
                    'name': node.name,
                    'docstring': ast.get_docstring(node),
                    'args': [{'name': arg.arg, 'annotation': annotation_to_string(arg.annotation)} for arg in node.args.args],
                    'returns': annotation_to_string(node.returns)
                }
                functions.append(function_info)
    
    return {
        "lines_of_code": lines_of_code,
        "imports": imports,
        "classes": classes,
        "functions": functions
    }

def annotation_to_string(annotation):
    """Convert annotation AST node to a string or return None if not annotated."""
    if annotation is None:
        return None
    elif isinstance(annotation, ast.Name):
        return annotation.id
    elif isinstance(annotation, ast.Attribute):
        return f"{annotation.value.id}.{annotation.attr}"
    elif isinstance(annotation, ast.Subscript):
        # Handle subscripted types like List[int]
        # This is a simplification; more complex generic types might need further handling.
        if hasattr(annotation.value, 'id') and hasattr(annotation.slice.value, 'id'):
            return f"{annotation.value.id}[{annotation.slice.value.id}]"
        else:
            return None
    return None

def get_docstring_report(data):
    """Generate a docstring report."""
    lines = []
    # Classes and their methods
    for cls in data['classes']:
        if cls['docstring']:
            lines.append(f"Class '{cls['name']}': {cls['docstring']}")
        else:
            lines.append(f"Class '{cls['name']}': DocString not found")

        for method in cls['methods']:
            if method['docstring']:
                lines.append(f"Method '{method['name']}' in class '{cls['name']}': {method['docstring']}")
            else:
                lines.append(f"Method '{method['name']}' in class '{cls['name']}': DocString not found")

    # Standalone functions
    for func in data['functions']:
        if func['docstring']:
            lines.append(f"Function '{func['name']}': {func['docstring']}")
        else:
            lines.append(f"Function '{func['name']}': DocString not found")
    
    return "\n\n".join(lines)  # separate each entry by empty line for clarity

def check_type_annotations(data):
    """Check for type annotations in functions and methods."""
    missing_annotations = []
    # Check standalone functions
    for func in data['functions']:
        if not has_type_annotations(func):
            missing_annotations.append(f"Function '{func['name']}'")

    # Check class methods
    for cls in data['classes']:
        for method in cls['methods']:
            if not has_type_annotations(method):
                missing_annotations.append(f"Method '{method['name']}' in class '{cls['name']}'")

    if missing_annotations:
        report = "Missing Type Annotations:\n" + "\n".join(f"- {item}" for item in missing_annotations)
        return report
    else:
        return "All functions and methods have type annotations."

def has_type_annotations(func):
    """Return True if the function/method has type annotations for all args and return type."""
    args_annotated = all(arg['annotation'] is not None for arg in func['args'])
    return_annotation = func['returns'] is not None
    return args_annotated and return_annotation

def check_naming_conventions(data):
    """Check naming conventions for classes, functions, and methods."""
    class_issues = []
    func_issues = []

    # Classes should be CamelCase
    for cls in data['classes']:
        if not re.match(r'^[A-Z][a-zA-Z0-9]*$', cls['name']):
            class_issues.append(f"Class '{cls['name']}' does not follow CamelCase")

        # Methods should be snake_case
        for method in cls['methods']:
            if not re.match(r'^[a-z_][a-z0-9_]*$', method['name']):
                func_issues.append(f"Method '{method['name']}' in class '{cls['name']}' does not follow snake_case")

    # Standalone functions should be snake_case
    for func in data['functions']:
        if not re.match(r'^[a-z_][a-z0-9_]*$', func['name']):
            func_issues.append(f"Function '{func['name']}' does not follow snake_case")

    if not class_issues and not func_issues:
        return "All names adhere to the specified naming convention."
    
    report_lines = []
    if class_issues:
        report_lines.append("Classes:")
        report_lines.extend(f"- {issue}" for issue in class_issues)
    if func_issues:
        report_lines.append("Functions/Methods:")
        report_lines.extend(f"- {issue}" for issue in func_issues)

    return "Naming Convention Issues:\n" + "\n".join(report_lines)

def generate_file_structure_report(data):
    """Generate the file structure section of the report."""
    report = []
    report.append(f"Total lines of code: {data['lines_of_code']}")
    if data['imports']:
        report.append("Imports:")
        for imp in data['imports']:
            report.append(f"- {imp}")
    else:
        report.append("No imports found.")
    
    if data['classes']:
        report.append("Classes:")
        for cls in data['classes']:
            report.append(f"- {cls['name']}")
    else:
        report.append("No classes found.")
    
    if data['functions']:
        report.append("Functions:")
        for func in data['functions']:
            report.append(f"- {func['name']}")
    else:
        report.append("No standalone functions found.")
    
    return "\n".join(report)

def generate_full_report(data):
    """Generate the full style report as a string."""
    structure_report = generate_file_structure_report(data)
    docstring_report = get_docstring_report(data)
    type_annotation_report = check_type_annotations(data)
    naming_report = check_naming_conventions(data)

    # Format final report
    final_report = []
    final_report.append("File Structure")
    final_report.append(structure_report)
    final_report.append("\nDoc Strings")
    final_report.append(docstring_report)
    final_report.append("\nType Annotation Check")
    final_report.append(type_annotation_report)
    final_report.append("\nNaming Convention Check")
    final_report.append(naming_report)

    return "\n".join(final_report)

def main():
    # If a file path is provided via argv, use it. Otherwise, prompt user.
    if len(sys.argv) == 2:
        filepath = sys.argv[1]
    else:
        filepath = input("Enter the path to the Python file: ").strip()

    if not os.path.isfile(filepath):
        print("File not found. Exiting.")
        sys.exit(1)

    data = parse_file_structure(filepath)
    report = generate_full_report(data)

    # Write report to a file
    filename = os.path.basename(filepath)
    report_filename = f"style_report_{filename}.txt"
    with open(report_filename, 'w') as f:
        f.write(report)
    
    print(f"Style report generated: {report_filename}")


if __name__ == "__main__":
    main()