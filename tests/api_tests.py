import unittest
import os
import shutil
import sys
import check50
import check50.api

class Base(unittest.TestCase):
    def setUp(self):
        self.filename = "foo.py"
        self.write("")
        self.process = None

    def tearDown(self):
        os.remove(self.filename)
        if self.process and self.process.process.isalive():
            self.process.kill()

    def write(self, source):
        with open(self.filename, "w") as f:
            f.write(source)

    def runpy(self):
        self.process = check50.run(f"python3 ./{self.filename}")

class TestExists(Base):
    def test_fileDoesNotExist(self):
        with self.assertRaises(check50.Failure):
            check50.exists("i_do_not_exist")

    def test_fileExists(self):
        check50.exists(self.filename)

class TestDiff(Base):
    def setUp(self):
        super().setUp()
        self.txt_filename = "foo.txt"
        with open(self.txt_filename, "w") as f:
            f.write("foo")

    def tearDown(self):
        super().tearDown()
        os.remove(self.txt_filename)

    def test_noDiff(self):
        self.write("foo")
        self.assertFalse(check50.diff(self.txt_filename, self.filename))

    def test_diff(self):
        self.write("bar")
        self.assertTrue(check50.diff(self.txt_filename, self.filename))

class TestRun(Base):
    def test_returnsProcess(self):
        process = check50.run("python3 ./{self.filename}")
        self.assertIsInstance(process, check50.api.Process)

class TestProcessKill(Base):
    def test_kill(self):
        self.runpy()
        self.assertTrue(self.process.process.isalive())
        self.process.kill()
        self.assertFalse(self.process.process.isalive())

class TestProcessStdin(Base):
    def test_expectPrompt_noPrompt(self):
        self.write("x = input()")
        self.runpy()
        with self.assertRaises(check50.Failure):
            self.process.stdin("bar", prompt=True)

    def test_expectPrompt(self):
        self.write("x = input('foo')")
        self.runpy()
        self.process.stdin("bar", prompt=True)
        self.assertTrue(self.process.process.isalive())

    def test_noPrompt(self):
        self.write("x = input()\n")
        self.runpy()
        self.process.stdin("bar")
        self.assertTrue(self.process.process.isalive())

class TestProcessStdout(Base):
    def test_noOut(self):
        self.runpy()
        out = self.process.stdout(timeout=.1)
        self.assertEqual(out, "")
        self.assertFalse(self.process.process.isalive())

        self.write("print('foo')")
        self.runpy()
        out = self.process.stdout()
        self.assertEqual(out, "foo\n")
        self.assertFalse(self.process.process.isalive())

    def test_out(self):
        self.runpy()
        with self.assertRaises(check50.Failure):
            self.process.stdout("foo")
        self.assertFalse(self.process.process.isalive())

        self.write("print('foo')")
        self.runpy()
        self.process.stdout("foo\n")

    def test_outs(self):
        self.write("print('foo')\nprint('bar')\n")
        self.runpy()
        self.process.stdout("foo\n")
        self.process.stdout("bar")
        self.process.stdout("\n")
        self.assertTrue(self.process.process.isalive())

    def test_outRegex(self):
        self.write("print('foo')")
        self.runpy()
        self.process.stdout(".o.")
        self.process.stdout("\n")
        self.assertTrue(self.process.process.isalive())

    def test_outNoRegex(self):
        self.write("print('foo')")
        self.runpy()
        with self.assertRaises(check50.Failure):
            self.process.stdout(".o.", regex=False)
        self.assertFalse(self.process.process.isalive())

class TestProcessStdoutFile(Base):
    def setUp(self):
        super().setUp()
        self.txt_filename = "foo.txt"
        with open(self.txt_filename, "w") as f:
            f.write("foo")

    def tearDown(self):
        super().tearDown()
        os.remove(self.txt_filename)

    def test_file(self):
        self.write("print('bar')")
        self.runpy()
        with open(self.txt_filename, "r") as f:
            with self.assertRaises(check50.Failure):
                self.process.stdout(f, regex=False)

        self.write("print('foo')")
        self.runpy()
        with open(self.txt_filename, "r") as f:
            self.process.stdout(f, regex=False)

    def test_file_regex(self):
        self.write("print('bar')")
        with open(self.txt_filename, "w") as f:
            f.write(".a.")
        self.runpy()
        with open(self.txt_filename, "r") as f:
            self.process.stdout(f)

class TestExit(Base):
    def test_exit(self):
        self.write("sys.exit(1)")
        self.runpy()
        with self.assertRaises(check50.Failure):
            self.process.exit(0)
        self.process.kill()

        self.write("sys.exit(1)")
        self.runpy()
        self.process.exit(1)

    def test_noExit(self):
        self.write("sys.exit(1)")
        self.runpy()
        exit_code = self.process.exit()
        self.assertEqual(exit_code, 1)

class TestProcessKill(Base):
    def test_kill(self):
        self.runpy()
        self.process.kill()
        self.assertFalse(self.process.process.isalive())

class TestProcessReject(Base):
    def test_reject(self):
        self.write("input()")
        self.runpy()
        self.process.reject()
        self.process.stdin("foo")
        with self.assertRaises(check50.Failure):
            self.process.reject()

    def test_noReject(self):
        self.runpy()
        with self.assertRaises(check50.Failure):
            self.process.reject()

if __name__ == '__main__':
    unittest.main()
