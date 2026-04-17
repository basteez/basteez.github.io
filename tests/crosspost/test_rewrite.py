from __future__ import annotations

from scripts.crosspost.rewrite import rewrite_body

POST_URL = "https://bstz.it/p/my-slug/"
SITE_URL = "https://bstz.it"


def test_rewrites_dotslash_relative():
    md = "![alt](./img/x.png)"
    assert rewrite_body(md, POST_URL, SITE_URL) == "![alt](https://bstz.it/p/my-slug/img/x.png)"


def test_rewrites_relative_with_subdir():
    md = "![alt](img/x.png)"
    assert rewrite_body(md, POST_URL, SITE_URL) == "![alt](https://bstz.it/p/my-slug/img/x.png)"


def test_rewrites_bare_filename():
    md = "![alt](x.png)"
    assert rewrite_body(md, POST_URL, SITE_URL) == "![alt](https://bstz.it/p/my-slug/x.png)"


def test_rewrites_root_relative():
    md = "![alt](/img/x.png)"
    assert rewrite_body(md, POST_URL, SITE_URL) == "![alt](https://bstz.it/img/x.png)"


def test_leaves_absolute_https_untouched():
    md = "![alt](https://other.example/x.png)"
    assert rewrite_body(md, POST_URL, SITE_URL) == md


def test_leaves_data_uri_untouched():
    md = "![alt](data:image/png;base64,AAAA)"
    assert rewrite_body(md, POST_URL, SITE_URL) == md


def test_leaves_mailto_untouched():
    md = "[Email me](mailto:me@example.com)"
    assert rewrite_body(md, POST_URL, SITE_URL) == md


def test_leaves_anchor_untouched():
    md = "[Top](#top)"
    assert rewrite_body(md, POST_URL, SITE_URL) == md


def test_rewrites_html_img_src():
    md = '<img src="img/y.png" alt="y">'
    assert 'src="https://bstz.it/p/my-slug/img/y.png"' in rewrite_body(md, POST_URL, SITE_URL)


def test_rewrites_html_img_src_root_relative():
    md = '<img src="/img/y.png" alt="y">'
    assert 'src="https://bstz.it/img/y.png"' in rewrite_body(md, POST_URL, SITE_URL)


def test_leaves_html_img_absolute_untouched():
    md = '<img src="https://other.example/y.png">'
    assert rewrite_body(md, POST_URL, SITE_URL) == md


def test_multiple_images_all_rewritten():
    md = "![](a.png)\n![](./b.png)\n![](/c.png)\n![](https://x/d.png)"
    out = rewrite_body(md, POST_URL, SITE_URL)
    assert "![](https://bstz.it/p/my-slug/a.png)" in out
    assert "![](https://bstz.it/p/my-slug/b.png)" in out
    assert "![](https://bstz.it/c.png)" in out
    assert "![](https://x/d.png)" in out
