---
layout: page
title: Home
feature_image: /assets/banner.webp
---


Latest blog posts:

{% for post in site.posts limit:5 %}
- [{{ post.title }}]({{ post.url }}) — {{ post.date | date: "%Y-%m-%d" }}
{% endfor %}
