## Examples

Currently the only example is a more featureful version of the _Quickstart_ included in the library's README. If you have any good ideas for more examples that would be helpful then don't hesitate to [raise an issue](https://github.com/LovecraftianHorror/subwinder/issues) about it.

### [Advanced Quickstart](advanced_quickstart.py)

The main features for this example cover:

- Searching for a large amount of subtitles for local files by walking the file tree
- Using a custom ranking function when searching to try and get yield better search results (and because we can)
- Showing a nice way to serialize/deserialize the `SearchResult`s to json (other formats would be a similar process) so that we keep the option to vote, comment, or report them after being able to view the subtitles first

Hopefully you'll see from this example that it's surprisingly easy to do some complicated stuff with the API.
