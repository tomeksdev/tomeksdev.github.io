<div class="tags-list">
  {%- assign tags = site.tags | sort -%}
  {%- if tags.size == 0 -%}
    <p>No tags yet.</p>
  {%- else -%}
    {%- for tag in tags -%}
      {%- assign tag_name = tag[0] -%}
      {%- assign posts = tag[1] -%}
      {%- assign anchor = tag_name | slugify -%}
      <section id="{{ anchor }}" class="tag-section">
        <h2>#{{ tag_name }}</h2>
        <ul>
          {%- for post in posts -%}
            <li><a href="{{ post.url | relative_url }}">{{ post.title }}</a> <small>{{ post.date | date: "%b %d, %Y" }}</small></li>
          {%- endfor -%}
        </ul>
      </section>
    {%- endfor -%}
  {%- endif -%}
</div>
