#!/usr/bin/env ruby
require "git"
repo = Git.open(".")
commit_count = repo.log.count
name = "com_#{commit_count}"
repo.add_tag(name)
repo.push("origin", name)
puts "Created tag: #{name}"