{%- assign entries = site.projects | sort: 'date' | reverse -%}
<div class="project-timeline">
  <ol>
    {%- for project in entries %}
      {%- assign align = forloop.index0 | modulo: 2 -%}
      <li class="timeline-entry {% if align == 0 %}timeline-left{% else %}timeline-right{% endif %}">
        <div class="point"></div>
        <a class="content" href="{{ project.url | relative_url }}">
          <span class="date">{{ project.date | date: "%Y" }}</span>
          <h3>{{ project.title }}</h3>
          <p>{{ project.summary | default: project.excerpt | strip_html | truncate: 200 }}</p>
        </a>
      </li>
    {%- endfor %}
  </ol>
</div>
