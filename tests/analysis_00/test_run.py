import analysis_00.run as test_module


def test_main(tmp_path):
    result = test_module.main(
        analysis_config={
            "output": tmp_path,
        },
    )
    assert result == {"outputs": []}
