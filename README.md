# easy-commit

**easy-commit** is an open-source AI agent that automatically generates smart commit messages by learning from real commits found on GitHub. The goal: simplify your commit process and make your project history clear, consistent, and professional.

## Why easy-commit?

Writing good commit messages is often overlooked, but it’s crucial for understanding a project’s evolution. With easy-commit, you no longer have to worry about crafting the perfect message—let AI do it for you, inspired by the best practices from thousands of real projects.

## Key Features

- 🧠 **Continuous learning**: The agent trains on real commit messages from GitHub, adapting to various styles and conventions.
- 🚀 **Automatic generation**: Instantly suggests relevant commit messages based on your changes.
- 📊 **Consistency and clarity**: Ensures your commit history is cleaner and more informative.
- 🔄 **Open-source**: Transparent, hackable, and community-driven.

## For formatting

### Instalation
```bash
pip install black flake8 isort
```
### Linting
```bash
flake8 my_script.pyy
# or
pylint my_script.py
````
### Formatting
```bash
black my_script.py
# or
isort my_script.py
```

## Coming Soon

A **CLI tool** will soon be available to use easy-commit from any terminal, on any project.  
⚠️ The CLI will be unstable at first—feedback and bug reports are welcome!

## Example Usage (upcoming CLI)

```bash
# Instantly generate a commit message from the terminal
easy-commit generate
```
More details and configuration options coming soon!

## Contributing
easy-commit is in its early days! Contributions are welcome, whether it’s on the AI, the CLI integration, documentation, or tests.
Feel free to open an issue or a pull request.

## License
MIT