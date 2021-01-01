## Examples

**Note: All of these examples assume that your credentials are set with environment variables as described in the [Authsubwinder initialization docs](https://github.com/LovecraftianHorror/subwinder/blob/master/docs/Authenticated-Endpoints.md#initialization)**

If you have any good ideas for more examples that would be helpful then don't hesitate to [raise an issue](https://github.com/LovecraftianHorror/subwinder/issues) about it.

### [Advanced Quickstart](advanced_quickstart.py)

The main features for this example cover:

- Searching for a large amount of subtitles for local files by walking the file tree
- Using a custom ranking function when searching to try and yield better search results (and because we can)
- Showing a nice way to serialize/deserialize the `SubtitlesInfo`s to JSON (other formats would be a similar process) so that we keep the option to vote on, comment on, or report them after being able to view the subtitles first

Hopefully you'll see from this example that it's surprisingly easy to do some complicated stuff with the API.

### [Interactive](interactive.py)

**Note: that searching this way is not trying to get an exact match like searching with a `MediaFile` object would**

This example covers:

- Getting information on the current user (name, download_info, etc.)
- Searching for the movie using a string (essentially a normal search on the website)
- Searching for, previewing, and downloading subtitles

### [Robust Searching](robust_search.py)

This example covers how you can make searching for subtitles more robust by falling back to guessing based on the filename (this may look like a lot at first, but everything is heavily commented on why I'm doing what I'm doing to try and help out).
