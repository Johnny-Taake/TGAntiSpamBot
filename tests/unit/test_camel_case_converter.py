from utils.camel_case_to_snake_case import camel_case_to_snake_case


class TestCamelCaseToSnakeCase:
    def test_simple_camel_case(self):
        """Test basic camelCase to snake_case conversion."""
        assert camel_case_to_snake_case("simpleTest") == "simple_test"

    def test_pascal_case(self):
        """Test PascalCase to snake_case conversion."""
        assert camel_case_to_snake_case("PascalCase") == "pascal_case"

    def test_single_word(self):
        """Test single word conversion."""
        assert camel_case_to_snake_case("Word") == "word"
        assert camel_case_to_snake_case("word") == "word"

    def test_acronym_handling(self):
        """Test handling of acronyms."""
        assert camel_case_to_snake_case("XMLParser") == "xml_parser"
        assert camel_case_to_snake_case("HTMLDocument") == "html_document"

    def test_consecutive_uppercase(self):
        """Test consecutive uppercase letters."""
        assert camel_case_to_snake_case("APIRequest") == "api_request"
        assert camel_case_to_snake_case("HTTPSConnection") == "https_connection"

    def test_complex_mixed_case(self):
        """Test more complex mixed cases."""
        assert camel_case_to_snake_case("iPhoneXMLParser") == "i_phone_xml_parser"
        assert camel_case_to_snake_case("getHTMLFromURL") == "get_html_from_url"

    def test_already_snake_case(self):
        """Test strings already in snake_case."""
        assert camel_case_to_snake_case("already_snake_case") == "already_snake_case"

    def test_empty_string(self):
        """Test empty string."""
        assert camel_case_to_snake_case("") == ""

    def test_single_character(self):
        """Test single character."""
        assert camel_case_to_snake_case("A") == "a"
        assert camel_case_to_snake_case("a") == "a"
