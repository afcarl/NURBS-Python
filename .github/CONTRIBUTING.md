# Contribution Guidelines

NURBS-Python is a free and open-source project released under [MIT License](../LICENSE). You are always welcome to 
contribute to NURBS-Python and it could happen in many ways!

The development started with the intentions of providing an object-oriented NURBS library in pure Python for 
scientific and research purposes. The author and all the contributors volunteered their free time to develop and 
improve this project, and I appreciate your time in using, developing and testing NURBS-Python.

Before you post, I would like to recommend some resources for starters:

* [Code of Conduct](CODE_OF_CONDUCT.md)
* [README file](../README.rst)
* [Official Documentation](http://nurbs-python.readthedocs.io/en/latest/)
* [The NURBS Book](http://www.springer.com/gp/book/9783642973857)


## Before you post, please read!

We have a nice [Code of Conduct](CODE_OF_CONDUCT.md) document and it describes pretty much everything you need to know
in the most appropriate way. Please see [Code of Conduct](CODE_OF_CONDUCT.md) for details.

In summary, it would be good to remember these before you post to the issue tracker or email the author:

* Remember that you are talking to humans
* Adhere to the same standards of behavior that you follow in your real life as you are talking to complete strangers
* Please be kind and respectful in your posts
* Please and please don't use stingy words or phrases
* Double-check your attitude in your posts
* Be reasonable
* Feel free to explain the problem as long as or as detailed as you would like to
* Simply, __be nice__!

The following will **NOT** be tolerated in any way:

* Any sort of offensive comment
* Contempt in explicit and/or implicit ways
* Any sort of accusation directed to the authors and/or contributors (that's why we have the LICENSE file)
* Complaints about implementation choices (instead, please ask about the reason nicely or fix it and create a PR)
* "Bad" tone in writing (i.e. please triple-check how you say what you would like to say)
* A strange thought that people who read the issue tracker have ability to read your mind (happens all the time)

I would like to remind that all authors and contributors spend their free time to put some effort on development of 
this package. Their free time is as valuable as your free time, the time you spend outside of your regular work doing 
non-work and completely unrelated things. Therefore, please show some respect in your messages. Horrible grammar, 
bad English, long explanations, etc. are all okay, no worries :-)

In case of any confusions or problems, please follow [this link](http://lmgtfy.com/?q=netiquette).

## What happens when you found a bug

* Please read __Before You Post__ rules (right above)
* Please make sure that you are using the latest version on the `master` branch.
* Please try to explain the problem as much as possible. I would be glad if you could write the steps to reproduce the
issue.
* If you have used `pip` to install the package, please indicate the version that you are using.
* Did I say details are very important?

## Coding Standards

You must follow the standards below when developing for the [the core library](http://nurbs-python.readthedocs.io/en/latest/modules.html) without any exceptions.

* Pure python code, i.e. no compilable code, including C/C++ code using Python's C API, Cython, etc.
* Using the modules that come with Python's standard library. Please note that NumPy, SciPy, etc. **are not** included in the standard library.
* Compatible (at least) with Python 2.7.x and 3.5.x together.
* It is acceptable to use very well-known backporting and helper modules like [functools32](https://pypi.org/project/functools32/) only if critically necessary. These modules must be installable via `pip` on all platforms without any issues or additional requirements.
* Soft dependencies are acceptable; e.g. if some module is installed, then use the functionality. Otherwise, use a custom or simplified implementation of it.
* Please don't mix the data types (lists, tuples, arrays, etc.)

Since all visualization components are considered as experimental, using external libraries (and even NumPy) are 
acceptable when developing new visualization components or improving the existing ones. 
You don't need to add them to `setup.py` as dependencies.

I would be glad if you could follow these standards while developing for NURBS-Python. Failure to follow may cause
rejection of your contributions (as pull requests or other methods).

## Feature requests

It could be always possible to add new features and the same rules are effective as if you have found a bug.
**I would be very much glad if you could directly develop the new features and make a pull request
instead of asking me to implement them** :)

## Pull requests

Please [create pull requests](https://help.github.com/articles/creating-a-pull-request/) against relevant branch.

* For NURBS-Python v4.x, PR against `master`
* For NURBS-Python v3.x, PR against `3.x`
* For NURBS-Python v2.x, PR against `2.x`

CI tools are set to test every pull request, and I would appreciate if you could add tests for your changes and test
your code with a Python linter utility, e.g. `pylint` and/or `prospector`.
 
All your changes will be reviewed and if they are accepted, they will be merged to the `master` branch in the next 
subsequent release of NURBS-Python and your name will be added to the [CONTRIBUTORS](../README.rst) file.

Feel free to open an issue on the project issue tracker, if you have any questions.

## Tests

The project includes automated tests under `'tests/` directory and all tests are designed to run with `pytest`.
I would appreciate if you could contribute more tests to increase their code coverage.

-----

As always, all contributions, such as constructive comments, ideas, code improvements and tests are much appreciated.

Thanks in advance!
