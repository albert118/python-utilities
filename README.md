# SetUp Notes and Guide

## 1.) Install Python

This project requires Python!!
Typically the latest is fine, however some issues arrise in always using the *VERY* latest
version. If you seem to be having issues with packages, try a slightly older release.

### Using Choco (typically the easiest way)

``` 
PS1:/ choco install python
```

### Or with an MSI Installer from the Web

(Simple download and MSI installer)[https://www.python.org/downloads/].

## 2.) Setup the virtualenv and pip-tools

Python development can get messy with packages. Pip helps a lot, but a 
virtualenv helps handle versioning consistancy of packages, and Python itself. 
Then, to make production and development instance dependencies more dependable
we rely on the pip-tools lib.

Before we install anything else, let's setup the virtualenv and pip-tools!

Note: DO NOT USE THE `--user` arg when installing content! This can create issues
with the PATH. Especially for Jupyter!

```
cd python-http-tools
python -m pip install virtualenv pip-tools
# setup a new virtualenv for project-package management
virtualenv .
# re-compile requirements for your local environment
pip-compile
```

This will setup the virtualenv in the current directory, but it needs to be
activated and deactivated when we use it. 
**I assume herein that you have activated the venv!**

```
Scripts\activate
(python-data-tools) C:\Users\source\repo\python-data-tools>
# do some work....💻
# ... then let's deactivate (because we want to work on a different project maybe)
Scripts\deactivate.bat
```

### Constraining and Including Development Requirements

If you plan to develop this repo, you will need to constrain the "prod" 
requirements with development extras. Simply run the below command to do so.
*Continued in 3. Development*

```
pip-compile dev-requirements.in
```

## 3.) Install the Python dependencies:

### "Production" - non-dev environs

Production setup is simple, just run the below command and dependencies 
will sync to your current virtualenvironment.

```
pip-sync
```

### Development

Assuming you constrained your requirements in step 2. you can now correctly
install the dev stage requirements like so,

```
pip-sync requirements.txt dev-requirements.txt
```

## 4.) Setup and Run the Jupyter Lab Notebook

Jupyter lab notebooks are an easy way to reproduce scripting results in a readable 
(and documentable) fashion.

If you have any issues starting Jupyter (deactivate the virtualenv) and uninstall
it from the System. Then reinstall it in the virtualenv, **DO NOT USE THE `--user`**
arg when installing!

To kick off the jupyterlab-server, run the startup command,

```
jupyter-lab
```

Running the command `jupyter-lab` should kick off a websocket app in the console and 
redirect you to your default browser. You're done! 🎈.