require 'jekyll/page_without_a_file'

module TomeksDEV
  class Pager
    attr_reader :page, :per_page, :posts, :total_pages, :total_posts,
                :previous_page, :next_page

    def initialize(page, all_posts, per_page, path_template)
      @page = page
      @per_page = [per_page, 1].max
      @path_template = path_template || '/page/:num/'
      @total_posts = all_posts.size
      @total_pages = (@total_posts.to_f / @per_page).ceil
      @total_pages = 1 if @total_pages.zero?
      @posts = all_posts.slice((page - 1) * @per_page, @per_page) || []
      @previous_page = page > 1 ? page - 1 : nil
      @next_page = page < total_pages ? page + 1 : nil
    end

    def previous_page_path
      page_path(previous_page)
    end

    def next_page_path
      page_path(next_page)
    end

    private

    def page_path(num)
      return '/' if num.nil? || num <= 1

      path = @path_template.sub(':num', num.to_s)
      path = "/#{path}" unless path.start_with?('/')
      Jekyll::URL.unescape_path(path)
    end
  end

  class PaginationGenerator < Jekyll::Generator
    safe true
    priority :lowest

    def generate(site)
      pagination_config = site.config['pagination'] || {}
      per_page = pagination_config['per_page'].to_i
      return if per_page <= 0

      path_template = pagination_config['path'] || '/page/:num/'

      index_page = site.pages.find { |p| p.url == '/' }
      return unless index_page

      all_posts = site.posts.docs.dup
      total_pages = (all_posts.size.to_f / per_page).ceil
      total_pages = 1 if total_pages.zero?

      (1..total_pages).each do |page_num|
        pager = Pager.new(page_num, all_posts, per_page, path_template)
        if page_num == 1
          index_page.data['paginator'] = pager
        else
          add_additional_page(site, index_page, pager, page_num, path_template)
        end
      end
    end

    private

    def add_additional_page(site, index_page, pager, page_num, path_template)
      path = path_template
      dir = path.sub(':num', page_num.to_s)
      dir = "/#{dir}" unless dir.start_with?('/')
      dir = File.join('/', dir).gsub(%r{//+}, '/')
      new_page = Jekyll::PageWithoutAFile.new(site, site.source, dir, 'index.html')
      new_page.content = index_page.content
      new_page.data = index_page.data.merge('paginator' => pager)
      site.pages << new_page
    end
  end
end
