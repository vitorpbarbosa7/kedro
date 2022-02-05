# Copyright 2020 QuantumBlack Visual Analytics Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND
# NONINFRINGEMENT. IN NO EVENT WILL THE LICENSOR OR OTHER CONTRIBUTORS
# BE LIABLE FOR ANY CLAIM, DAMAGES, OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF, OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# The QuantumBlack Visual Analytics Limited ("QuantumBlack") name and logo
# (either separately or in combination, "QuantumBlack Trademarks") are
# trademarks of QuantumBlack. The License does not grant you any right or
# license to the QuantumBlack Trademarks. You may not use the QuantumBlack
# Trademarks or any confusingly similar mark as a trademark for your product,
#     or use the QuantumBlack Trademarks in any other manner that might cause
# confusion in the marketplace, including but not limited to in advertising,
# on websites, or on software.
#
# See the License for the specific language governing permissions and
# limitations under the License.


Feature: Run Project


  Scenario: Run default python entry point with example code

    Local environment should be used by default when no env option is specified.

    Given I have prepared a config file with example code
    And I have run a non-interactive kedro new
    And I have updated kedro requirements
    And I have executed the kedro command "install"
    When I execute the kedro command "run"
    Then I should get a successful exit code
    And the console log should show that 4 nodes were run
    And "local" environment was used

  Scenario: Run parallel runner with default python entry point with example code
    Given I have prepared a config file with example code
    And I have run a non-interactive kedro new
    And I have updated kedro requirements
    And I have executed the kedro command "install"
    When I execute the kedro command "run --parallel"
    Then I should get a successful exit code
    And the console log should show that "split_data" was run
    And the console log should show that "train_model" was run
    And the console log should show that "predict" was run
    And the console log should show that "report_accuracy" was run
    And "local" environment was used

  Scenario: Run default python entry point without example code
    Given I have prepared a config file without example code
    And I have run a non-interactive kedro new
    And I have updated kedro requirements
    And I have executed the kedro command "install"
    When I execute the kedro command "run"
    Then I should get an error exit code
    And I should get an error message including "Pipeline contains no nodes"

  Scenario: Run kedro run with config file
    Given I have prepared a config file with example code
    And I have run a non-interactive kedro new
    And I have prepared a run_config file with config options
    And I have updated kedro requirements
    And I have executed the kedro command "install"
    When I execute the kedro command "run --config run_config.yml"
    Then I should get a successful exit code
    And the console log should show that 1 nodes were run

  Scenario: Run kedro run with config file and override option
    Given I have prepared a config file with example code
    And I have run a non-interactive kedro new
    And I have prepared a run_config file with config options
    And I have updated kedro requirements
    And I have executed the kedro command "install"
    When I execute the kedro command "run --config run_config.yml --pipeline __default__"
    Then I should get a successful exit code
    And the console log should show that 4 nodes were run
