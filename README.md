# Insiders

$redesign$ $sketch$ $work$

---

## What

There's a much cleaner `mkdocs` under the hood, waiting to be let out.

*This is a space for design exploration.*

At the same time we also need to continue to improve mkdocs as it currently stands.
I'm planning on taking a dual approach here...

* Incremental improvements to the existing `mkdocs`. *(As a minimum the default theme needs freshening up.)*
* Explore this design space, and determine how we can best move forward in places where more fundamental changes are required.

## Core design themes

*TODO: Expand on this.*

#### １ A clean obvious build context for themes to work with.

https://github.com/mkdocs/insiders/blob/main/mkdocs/site.py

#### ２ Templating over code.

Safe rendering, avoid Python knowledge as a dependancy.

#### ３ Kiss.

Onboarding etc.

## Give it a whirl

```
git clone https://github.com/encode/httpx
cd httpx
python -m venv venv
venv/bin/pip install git+https://github.com/mkdocs/sketch
venv/bin/mkdocs serve
```

<img width="1230" alt="image" src="https://github.com/mkdocs/sketch/assets/647359/d94d3325-750c-4c13-a4fb-60c1422173d7">

## What's the big deal

* `mkdocs serve` renders pages on the fly. There's no "build the whole site" process needed.
* The context passed to the theme [is completely cleaned up](https://github.com/mkdocs/sketch/blob/main/mkdocs/site.py). I'll write about this as we go, there's a really clean clear data model that's passed through to the templating.
* More to come...
