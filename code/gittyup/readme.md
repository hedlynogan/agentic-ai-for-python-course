# Gitty Up

This is an application which will work as a CLI tool for developers.

## The problem

When working on multiple computers or with many team members, and across many projects, it's easy to start working on an existing one and forget to do a `git pull`. Then when it's time to commit the changes, you realize you have merge conflicts and more. This is not fun.

## The solution

This application will be run in a folder at the root of source code. It will traverse the current dir and all subdirs. Whenever it discovers a git repo, it will run the shell command `git pull --all`. This will ensure that every project in this directory tree is up to date and ready to roll.

We want to be sure to employ color to communicate to our users. Feel free to include the colorma python package for this.
