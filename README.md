# Ntail Django Copier Template

Welcome to the Ntail Django project template! We use [Copier](https://copier.readthedocs.io/) to manage this boilerplate. Copier makes it super easy to scaffold a fresh Django project and, more importantly, keeps your project updated whenever we make changes to this upstream template.

This guide will walk you through generating a new project from scratch.

## Prerequisites

Before you start, make sure you have the following installed on your machine:
- [uv](https://docs.astral.sh/uv/) (An extremely fast Python package and project manager)
- Git

You don't even need to install Python manually or use tools like `pyenv` or `pipx`. `uv` will handle all the Python versioning and package management for you!

You'll need `copier` installed as a global tool. You can easily do this with `uv`:

```bash
uv tool install copier
```

## Scaffolding a New Project

To generate a new project, open your terminal, navigate to the directory where you want your new project to live, and run:

```bash
copier copy git@github.com:MacFF/django-copier-template.git my-new-project-dir
```
*(Note: You can replace `my-new-project-dir` with the name of the folder you want to create).*

### The Prompts

Copier will ask you a couple of quick questions to configure your new project. Don't worry, it's short:

1. **`project_name`**: The human-readable name of your project (e.g., `My Awesome Project`).
2. **`project_slug`**: The machine-readable name used for folders and Python packages. It usually defaults to a snake_case version of your project name (e.g., `my_awesome_project`).

Once you answer these, Copier will generate the files and put them in `my-new-project-dir`.

## What's Next? (Post-Generation Steps)

Alright, your project is generated! Here's how to get it running locally. We will use `uv` for all the heavy lifting.

1. **Navigate to your new project:**
   ```bash
   cd my-new-project-dir
   ```

2. **Sync the project and install dependencies:**
   Instead of manually creating a virtual environment and running `pip install`, just use `uv sync`. This will automatically fetch the correct Python version, create an isolated virtual environment (`.venv`), and lock and install all dependencies defined in your project.
   ```bash
   uv sync
   ```

3. **Environment Variables:**
   Copy the example environment file and fill in your local credentials (like database URLs, secret keys, etc.).
   ```bash
   cp .env_example .env
   ```

4. **Run Migrations:**
   Initialize your local database. By prefixing the command with `uv run`, `uv` automatically executes it inside the project's virtual environment—no manual activation (`source .venv/bin/activate`) required!
   ```bash
   uv run python manage.py migrate
   ```

5. **Fire it up:**
   Start the Django development server.
   ```bash
   uv run python manage.py runserver
   ```
   Check it out at `http://localhost:8000`.

## Keeping Your Project Updated

One of the best things about Copier is that you can pull in updates from this template later on. 

If we fix a bug or add a cool new feature to this template, you don't have to manually copy-paste the changes. Just go to your project root and run:

```bash
copier update
```

Copier will check the template for changes, apply them to your project, and ask you to resolve any git conflicts if you've heavily modified the generated files. It's basically magic.

---
Happy coding! If you run into any weird issues, feel free to open an issue in this repository.
