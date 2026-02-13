---
layout: page
title: Blog
permalink: /blog/
feature_image: /assets/banner.webp
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
