# Set up PyCharm

> *Note:* This documentation is based on `Kedro 0.16.4`, if you spot anything that is incorrect then please create an [issue](https://github.com/quantumblacklabs/kedro/issues) or pull request.

This section will present a quick guide on how to configure [PyCharm](https://www.jetbrains.com/pycharm/) as a development environment for working on Kedro projects.

Open a new project directory in PyCharm. You will need to add your **Project Interpreter**, so go to **PyCharm | Preferences** for macOS or **File | Settings** for Windows and Linux:

![Pycharm Preferences graphic](../meta/images/pycharm_preferences.png)

Choose **Project Interpreter**: <br />

![Project Interpreter graphic](../meta/images/pycharm_project_interpreter.png)

Click the cog on the right-hand side and click **Add**:

![Add interpreter graphic](../meta/images/pycharm_add_interpreter.png)

Select **Conda Environment**:

![Add conda environment graphic](../meta/images/pycharm_add_conda_env.png)

Choose **Existing environment** and navigate your way to find your existing environment. If you don't see your `conda` environment in the dropdown menu then you need to open a `terminal` / `command prompt` with your `conda` environment activated and run:

```console
# macOS / Linux
which python
# Windows
python -c "import sys; print(sys.executable)"
```

Paste the interpreter path into the file picker and click **OK**: <br />

![Paste interpreter patch graphic](../meta/images/pycharm_select_conda_interpreter.png)

Finally, in the **Project Explorer** right-click on `src` and then go to **Mark Directory as | Sources Root**:

![Mark directory as sources root graphic](../meta/images/pycharm_mark_dir_as_sources_root.png)


## Set up Run configurations

[PyCharm Run configurations](https://www.jetbrains.com/help/pycharm/creating-and-editing-run-debug-configurations.html) allow you to execute preconfigured scripts rapidly in your IDE with a click of a button. This may be useful for testing, running and packaging your Kedro projects.

Here we will walk you through an example of how to setup Run configuration for Kedro CLI `run` command, however it is also applicable to other Kedro commands: `test`, `install`, `package`, `build-docs`.

Go to **Run | Edit Configurations**:

![Run | Edit Configurations graphic](../meta/images/pycharm_edit_confs.png)

Add a new **Python** Run configuration:

![Add a new Python run configuration graphic](../meta/images/pycharm_add_py_run_config.png)

Create a **Run / Debug Configuration** for `kedro run` and get the path to the Kedro CLI script:

```console
# macOS / Linux
which kedro

# Windows (in `cmd`)
python -c "import sys, os.path; print(os.path.join(os.path.dirname(sys.executable), 'Lib\site-packages\kedro\__main__.py'))"
```

Edit the new Run configuration as follows:

![Edit the new configuration graphic](../meta/images/pycharm_edit_py_run_config.png)

Replace **Script path** with path obtained above and **Working directory** with the path of your project directory and then click **OK**.

To execute the Run configuration, select it from the **Run / Debug Configurations** dropdown in the toolbar (if that toolbar is not visible, you can enable it by going to **View > Toolbar**). Click the green triangle:

![Execute the Run configuration graphic](../meta/images/pycharm_conf_run_button.png)

You may also select **Run** from the toolbar and execute from there. <br />

![Select Run from the toolbar graphic](../meta/images/pycharm_conf_run_dropdown.png)

For other `kedro` commands, follow same steps but replace `run` in the `Parameters` field with the other commands that are to be used (e.g., `test`, `package`, `build-docs` etc.).


## Debugging

To debug, simply click the line number in the source where you want execution to break:

![Add a breakpoint to the source graphic](../meta/images/pycharm_add_breakpoint.png)

Then click the bug button in the toolbar (![](../meta/images/pycharm_debugger_button.png)) and execution should stop at the breakpoint:

![Click the bug button to debug graphic](../meta/images/pycharm_debugger_break.png)

>For more information about debugging with PyCharm take a look at the [debugging guide on jetbrains.com](https://www.jetbrains.com/help/pycharm/part-1-debugging-python-code.html).


## Advanced: Remote SSH interpreter

> *Note:* This section uses the features supported in PyCharm Professional Edition only.

Firstly, add an SSH interpreter. Go to **Preferences | Project Interpreter** as above and proceed to add a new interpreter. Select **SSH Interpreter** and fill in details of the remote computer:

![Select SSH Interpreter graphic](../meta/images/pycharm_ssh_interpreter_1.png)

Click **Next** and add the SSH password or SSH private key:

![Add SSH password/private key graphic](../meta/images/pycharm_ssh_interpreter_2.png)

Click **Next** and add the path of the remote interpreter. Assuming a Unix-like OS, this can be found by running `which python` within the appropriate `conda` environment on the remote computer.

![Add path to remote interpreter graphic](../meta/images/pycharm_ssh_interpreter_3.png)

Click **Finish**. Go to **Run / Debug Configurations** to add a **Remote Run**. Select the remote interpreter that you have just created. For the script path, get the path of the Kedro CLI on the remote computer by running `which kedro` (macOS / Linux) in the appropriate environment.

![Add a remote runner graphic](../meta/images/pycharm_ssh_runner.png)

Click **OK** and then select **Remote Run** from the toolbar and click **Run** to execute remotely.

![Select remote run graphic](../meta/images/pycharm_remote_run.png)

To remotely debug, click the debugger button as [described above](#debugging).

## Configuring the Kedro catalog validation schema

You can enable the Kedro catalog validation schema in your PyCharm IDE to enable real-time validation, autocompletion and see information about the different fields in your `catalog` as you write it. To enable this, open a `catalog.yml` file and you should see "No JSON Schema" in the bottom right corner of your window. Click it and select "Edit Schema Mapping".

![Edit schema mapping graphic](../meta/images/pycharm_edit_schema_mapping.png)

Add a new mapping using the "+" button in the top left of the window and select the name you want for it. Enter this URL `https://raw.githubusercontent.com/quantumblacklabs/kedro/develop/static/jsonschema/kedro-catalog-0.16.json` in the "Schema URL" field and select "JSON Schema Version 7" in the "Schema version" field.

Add the following file path pattern to the mapping: `conf/**/*catalog*`.

![Add file path pattern to mapping graphic](../meta/images/pycharm_catalog_schema_mapping.png)

> Different schemas for different Kedro versions can be found [here](https://github.com/quantumblacklabs/kedro/tree/develop/static/jsonschema).
