{ lib
, buildPythonPackage
, fetchPypi
, pythonOlder
, charset-normalizer
, dateparser
, lxml
, pytestCheckHook
, python-dateutil
, urllib3
, backports-datetime-fromisoformat
}:

buildPythonPackage rec {
  pname = "htmldate";
  version = "1.4.3";
  format = "setuptools";

  disabled = pythonOlder "3.6";

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-7FDwhLmX/fayb4wxRH5XifTetx/mk0LNodevDJ+R4Bs=";
  };

  propagatedBuildInputs = [
    charset-normalizer
    dateparser
    lxml
    python-dateutil
    urllib3
  ] ++ lib.optionals (pythonOlder "3.7") [
    backports-datetime-fromisoformat
  ];

  nativeCheckInputs = [
    pytestCheckHook
  ];

  # disable tests that require an internet connection
  disabledTests = [
    "test_input"
    "test_cli"
    "test_download"
  ];

  pythonImportsCheck = [ "htmldate" ];

  meta = with lib; {
    description = "Fast and robust extraction of original and updated publication dates from URLs and web pages";
    homepage = "https://htmldate.readthedocs.io";
    changelog = "https://github.com/adbar/htmldate/blob/v${version}/CHANGELOG.md";
    license = licenses.gpl3Plus;
    maintainers = with maintainers; [ joopitz ];
  };
}
