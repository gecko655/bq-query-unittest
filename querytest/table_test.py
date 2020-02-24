from .table import Table, ColumnMeta, Schema, TemporaryTables
from pathlib import Path
import pytest

class TestTable:
    def test_table(self):
        p = Path(__file__).parent / 'testdata/test1.csv'
        schema = [
            ('name', 'STRING'),
            ('category', 'STRING'),
            ('value', 'INT64'),
        ]

        assert Table(str(p), schema)

    def test_to_sqlを呼び出すとデータから一時テーブルを作成できる(self):
        p = Path(__file__).parent / 'testdata/test1.csv'
        schema = [
            ('name', 'STRING'),
            ('category', 'STRING'),
            ('value', 'INT64'),
        ]
        t = Table(str(p), schema, 'TEST_DATA')
        w = t.to_sql()
        assert w == """TEST_DATA AS (
SELECT * FROM UNNEST(ARRAY<STRUCT<name STRING, category STRING, value INT64>>
[("abc","bdc",200),("ほげほげ","ふがふが",300000)]
)
)"""

    def test_dataframe_to_string_list(self):
        p = Path(__file__).parent / 'testdata/test2.json'
        t = Table(str(p), [('name', 'STRING'),('category', 'STRING'),('value', 'INT64'),], 'TEST_DATA')

        assert t.dataframe_to_string_list() == [['"abc"', '"bcd"', '300'], ['"ddd"', '"ccc"', '400'], [r'"\"xxx\""', '"yyy"', '123'], [r'"\"xxx\""',r'"[\"y\",\"y\",\"y\"]"','123']]

    def test_sql_stringによってリストからsqlのレコードが生成できる(self):
        input_list = [['"abc"', '"bcd"', '300'], ['"ddd"', '"ccc"', '400'], [r'"\"xxx\""', '"yyy"', '123']]
        assert Table.sql_string(input_list) == r'[("abc","bcd",300),("ddd","ccc",400),("\"xxx\"","yyy",123)]'

class TestColumnMeta:
    def test_STRINGは使えるタイプ(self):
        assert ColumnMeta('name', 'STRING')

    def test_ARRAYは使えるタイプ(self):
        assert ColumnMeta('name', 'ARRAY<STRING>')

    def test_ARRAYにはカッコが必要(self):
        with pytest.raises(AssertionError):
            ColumnMeta('name', 'ARRAY')

    def test_strで文字列に変更できる(self):
        assert str(ColumnMeta('name', 'STRING')) == 'name STRING'

    def test_nameに改行や空白文字カンマは入れられない(self):
        with pytest.raises(AssertionError):
            assert ColumnMeta('\n', 'STRING')
        with pytest.raises(AssertionError):
            assert ColumnMeta('a b', 'STRING')
        with pytest.raises(AssertionError):
            assert ColumnMeta(',', 'STRING')

    def test_使えないタイプを入れるとAssertionError(self):
        with pytest.raises(AssertionError):
            ColumnMeta('name', 'INTEGER')

    def test_空文字列はAssertionError(self):
        with pytest.raises(AssertionError):
            ColumnMeta('', 'ARRAY<STRING>')

    @pytest.mark.skip(reason='ARRAYの直下にARRAYは入れられないが、バグっている')
    def test_ARRAYの直下にARRAYは入れられない(self):
        with pytest.raises(AssertionError):
            ColumnMeta('name', 'ARRAY<ARRAY<STRING>>')

class TestSchema:
    def test_スキーマを生成できる(self):
        assert Schema([('name', 'STRING'), ('value', 'INT64')])

    def test_スキーマは空配列から生成しようとするとAssertionErrorになる(self):
        with pytest.raises(AssertionError):
            assert Schema([])

    def test_スキーマはstrでSTRUCTに変換できる(self):
        s = Schema([('time', 'TIMESTAMP'), ('event', 'STRING'), ('id', 'INT64')])
        assert str(s) == 'STRUCT<time TIMESTAMP, event STRING, id INT64>'

class TestTemporalTable:
    def test_一時テーブルのインスタンスが作成できる(self):
        pairs = [
            [
                str(Path(__file__).parent / 'testdata/test2.json'),
                [('name', 'STRING'),('category', 'STRING'),('value', 'INT64'),],
                'TEST_DATA1',
            ],
            [
                str(Path(__file__).parent / 'testdata/test1.csv'),
                [('name', 'STRING'),('category', 'STRING'),('value', 'INT64'),],
                'TEST_DATA2',
            ],
        ]

        assert TemporaryTables(pairs)

    def test_一時テーブルのインスタンスからSQLを生成できる(self):
        pairs = [
            [
                str(Path(__file__).parent / 'testdata/test2.json'),
                [('name', 'STRING'),('category', 'STRING'),('value', 'INT64'),],
                'TEST_DATA1',
            ],
            [
                str(Path(__file__).parent / 'testdata/test1.csv'),
                [('name', 'STRING'),('category', 'STRING'),('value', 'INT64'),],
                'TEST_DATA2',
            ],
        ]

        assert TemporaryTables(pairs).to_sql() == r'''WITH TEST_DATA1 AS (
SELECT * FROM UNNEST(ARRAY<STRUCT<name STRING, category STRING, value INT64>>
[("abc","bcd",300),("ddd","ccc",400),("\"xxx\"","yyy",123),("\"xxx\"","[\"y\",\"y\",\"y\"]",123)]
)
),TEST_DATA2 AS (
SELECT * FROM UNNEST(ARRAY<STRUCT<name STRING, category STRING, value INT64>>
[("abc","bdc",200),("ほげほげ","ふがふが",300000)]
)
)'''

@pytest.mark.skip(reason='BigQueryには直接クエリを発行しない')
def test_test():
    from google.cloud import bigquery

    # Construct a BigQuery client object.
    client = bigquery.Client()

    query = """
        SELECT word, word_count
        FROM `bigquery-public-data.samples.shakespeare`
        WHERE corpus = @corpus
        AND word_count >= @min_word_count
        ORDER BY word_count DESC;
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("corpus", "STRING", "romeoandjuliet"),
            bigquery.ScalarQueryParameter("min_word_count", "INT64", 250),
        ]
    )
    query_job = client.query(query, job_config=job_config)  # Make an API request.

    assert query_job
