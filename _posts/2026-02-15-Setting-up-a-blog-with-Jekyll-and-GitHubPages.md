---
layout: post
title: "How to set up this blog with Jekyll and GitHub pages"
date: 2026-02-15 12:00:00 +0000
---

On [GitHub Pages](https://docs.github.com/en/pages) you can host websites like this one for free. There are tons of tutorials out there, here I'm just sharing how I set up this very blog you're reading.


By default GitHub Pages uses Jekyll for building your website but they will [also accept](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site#static-site-generators) already built static files or your own workflow for building your website.

## Installation and Setup

We will be using `Jekyll` and `bundler` so we can locally preview the website while working on it.

To install Jekyll we'll first install ruby.
On *Linux* or *Windows Subsystem for Linux* (WSL) we install like this:
```bash
sudo apt install ruby-full build-essential zlib1g-dev
```
On a mac we do:
```bash
brew install ruby
```

Next we install `bundler` which we will use to manage the ruby plugins.
```bash
gem install bundler
```
We'll make our project directory and call it `my_jekyll_website`
```bash
mkdir my_jekyll_website
cd my_jekyll_website
```
To setup our project we record our dependencies in the `Gemfile`.

`Gemfile`
```ruby
source 'https://rubygems.org'
gem "github-pages", group: :jekyll_plugins
gem "jekyll-remote-theme"
```
We are using the `github-pages` plugin so we can test locally.
The `jekyll-remote-theme` plugin lets us use themes other than those [preconfigured](https://github.com/pages-themes) for GitHub Pages. We will show in the next titled section how to use a `remote theme`.

Next we'll add jekyll to the `Gemfile` like so:
```bash
bundle add jekyll
```
This will pin a specific version of jekyll, in my case `3.10`.

Now we install all the dependencies
```bash
bundle install
```

## Minimal viable website

### Starting jekyll server
If we want jekyll to start serving a webpage from our directory, we run the following command.
```bash
bundle exec jekyll serve --watch
```
This will keep jekyll running and refreshing as we make changes. 
The initial output should show us something like this:
```log
To use retry middleware with Faraday v2.0+, install `faraday-retry` gem
            Source: /home/myuser/my_jekyll_website
       Destination: /home/myuser/my_jekyll_website/_site
 Incremental build: disabled. Enable with --incremental
      Generating... 
                    done in 1.573 seconds.
 Auto-regeneration: enabled for '/home/myuser/my_jekyll_website'
    Server address: http://127.0.0.1:4000
  Server running... press ctrl-c to stop.
```
This also creates a directory called `_site` which jekyll has populated with an assets folder:
```bash
ls -la _site
```
```log
total 12
drwxrwxr-x 3 tobsecret tobsecret 4096 Feb  5 22:33 .
drwxrwxr-x 3 tobsecret tobsecret 4096 Feb  5 22:33 ..
drwxrwxr-x 3 tobsecret tobsecret 4096 Feb  5 22:33 assets
```

If we now go to [http://127.0.0.1:4000](http://127.0.0.1:4000) we see jekyll is serving up the file structure of our `_site` directory:
![Minimal Jekyll Website Screenshot](/assets/blog/2026-02-15/minimal_jekyll_screenshot.png "What Jekyll serves you in a directory empty besides the Gemfile")

This `_site` directory can have a lot of files in it, so we'd like to not have those show up when we use `git` for version control, so we'll make a `.gitignore` file to ignore this and a few other artefacts that Jekyll can create:

`.gitignore`
```
_site
.jekyll-cache
.sass-cache
```
### Adding first content

I am using a Jekyll template called [Alembic](https://github.com/daviddarnes/alembic) for my blog which comes with a nice default setup. 
In our `_config.yml` we'll tell Jekyll to use the `jekyll-remote-theme` plugin and specify the `remote_theme: daviddarnes/alembic@main`. In the `navigation_header` section we'll specify two sections: `Home` and `Blog`. For our webpage this will generate a Home and a Blog link at the top of every page in the navigation header.

`_config.yml`
```yml
title: Tobsecret's homepage
description: Programming Blog & Dominion sets
plugins:
  - jekyll-remote-theme
remote_theme: daviddarnes/alembic@main

# 9. Site navigation
navigation_header:
- title: Home
  url: /
- title: Blog
  url: /blog/

```
The paths in the `navigation_header` section specify the path in our directory where jekyll should be looking for a file called `index.md` that has the content for the page.

So for our `Home` page it will look in `/`, so directly in our project directory.

`index.md`
{% raw %}
```markdown
---
layout: page
title: Home
---


---

Latest blog posts:
{% for post in site.posts limit:5 %}
- [{{ post.title }}]({{ post.url }}) — {{ post.date | date: "%Y-%m-%d" }}
{% endfor %}
```
{% endraw %}
`layout: page` is important since `Alembic` predefines the layouts for `page` and `post`, i.e. those pages will get the navigation header and other features of `Alembic`.

The little loop in the `index.md` grabs the latest 5 posts from the `_posts` folder by their `date` field.

If we refresh our page, it should now look like this:
![minimal_config_alembic_screenshot.png](/assets/blog/2026-02-15/minimal_config_alembic_screenshot.png "Notice the header now has two links")
Notice the header now has two links, one to `Home` and one to `Blog`.


If we clicked on `Blog` we would get a `404: File Not Found`.

To populate that page we'd have to make another page `blog/index.md` which I'd just copy what the template uses:

{% raw %}
```markdown
---
layout: page
title: Blog
permalink: /blog/
---


{% if site.posts.size == 0 %}
No posts yet. Create posts in the `_posts` folder.
{% else %}
<ul>
{% for post in site.posts %}
  <li><a href="{{ post.url }}">{{ post.title }}</a> — {{ post.date | date: "%Y-%m-%d" }}</li>
{% endfor %}
</ul>
{% endif %}
```
{% endraw %}
![empty_blog_screenshot.png](/assets/blog/2026-02-15/empty_blog_screenshot.png)

Now if we wanted to add our first post, so something actually shows up in the blog, we want to create a file `_posts/2026-02-15-first-post.md`:

```markdown
---
layout: post
title: "Writing helps me think"
date: 2026-02-15 12:00:00 +0000
---
When I write about the software I write, I find myself looking up a lot more questions than when I am just getting things done.
```
And now our blog page is updated:
![updated_blog_post_view](/assets/blog/2026-02-15/updated_blog_post_view.png)

You can similarly also copy the `Search` section by adding a section in the `navigation_header` section of your `_config.yml`:

```yaml
navigation_header:
- title: Home
  url: /
...
- title: Search
  url: /search/
```

and copying over the `search/index.md`:
{% raw %}
```markdown
---
title: Search
excerpt: "Search for a page or post you're looking for"
---

{% include site-search.html %}
```
{% endraw %}
