---
layout: page
title: Home
---

Welcome to my site!
My name is Tobi and I enjoy thinking about software.
Besides the software blog I also have a Dominion section where I catalogue sets of cards my friends and I have found to be fun.


Latest blog posts:

{% for post in site.posts limit:5 %}
- [{{ post.title }}]({{ post.url }}) — {{ post.date | date: "%Y-%m-%d" }}
{% endfor %}