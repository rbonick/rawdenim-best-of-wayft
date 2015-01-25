import mimetypes
import re
import datetime
import praw

__author__ = 'rbonick'

# Based on code by David Ziegler at https://github.com/dziegler/redditfashion/blob/master/scripts/top.py

DEFAULT_SCORE_THRESHOLD = 15


def get_url_type(url):
    """
    Tries to guess whether an URL points to an image.
    """
    link_type, link_encoding = mimetypes.guess_type(url)

    if link_type is None:
        return "link"

    return "image" if link_type.startswith("image/") else "link"


class RunLength:
    MONTH = "month"
    YEAR = "year"


class WAYFTScraper:
    AUTOMOD = "RawDenimAutoMod"

    # Regex to extract URLs out of comment bodies
    html_link_pattern = re.compile('a href=\"([^\"]+)\"')

    def __init__(self):
        self.user_agent = "Top of WAYFT Collector"
        self.subreddit = "rawdenim"

    def scrape(self, score_threshold=DEFAULT_SCORE_THRESHOLD, run_length=RunLength.MONTH,
               month=datetime.date.today().month, year=datetime.date.today().year, author=AUTOMOD):
        reddit = praw.Reddit(user_agent=self.user_agent)

        query = "title:WAYFT AND author:{}".format(author)
        posts = reddit.search(query, self.subreddit, sort="new", limit=None)

        comments = []

        for submission in posts:
            # Ignore if not submitted this month/year
            submission_date = datetime.date.fromtimestamp(int(submission.created_utc))

            if submission_date.year != year:
                continue

            if run_length is RunLength.MONTH:
                if submission_date.month != month:
                    continue

            print "Checking {}, posted {}".format(submission.title, submission_date)

            for comment in submission.comments:
                if isinstance(comment, praw.objects.MoreComments):
                    continue

                if comment.score > score_threshold:
                    comments.append(comment)

        print "Found {} comments".format(len(comments))
        comments.sort(key=lambda comment: comment.score, reverse=True)
        self.get_photos(comments)

    def get_photos(self, comments):
        """
        I don't really understand this formatting, so I'm not going to touch it. Should probably use
        some kind of template library though.
        """

        all_image_urls = []

        for rank, comment in enumerate(comments, 1):

            urls = self.get_urls_from_comment(comment)

            if not urls:
                continue

            # Print informations about the post: rank, permalink, author and score
            print u"{}. [Post]({}) by *{}* (+{})  ".format(rank, comment.permalink, comment.author, comment.score)

            buckets = {
                "link": [],
                "image": [],
            }

            for url in urls:
                buckets[get_url_type(url)].append(url)

            # Print 4 spaces (actually only 3 because Python prints the 4th) to
            # let MarkDown indent the current line on the list item level.
            print "   ",

            # Print all links by their category
            for key, values in buckets.items():
                if not values:
                    continue

                if key == "image":
                    all_image_urls.extend(values)

                name = key.capitalize()
                for index, url in enumerate(values, 1):
                    print "[{} {}]({})".format(name, index, url)

        print "\n==========="
        print "Image links"
        print "==========="
        for img in all_image_urls:
            print img

    def get_urls_from_comment(self, comment):
        """
        Returns a list of all URLs in a comment.
        """
        return re.findall(self.html_link_pattern, comment.body_html)


if __name__ == "__main__":

    from optparse import OptionParser
    parser = OptionParser()

    parser.add_option(
        "-m",
        "--month",
        choices=map(str, range(1, 13)),
        dest="month",
        help="The month to scrape, defaults to current",
        default=datetime.date.today().month
    )
    parser.add_option(
        "-y",
        "--year",
        dest="year",
        help="The year to scrape, defaults to current",
        type='int',
        default=datetime.date.today().year
    )

    parser.add_option(
        "-s",
        "--score_threshold",
        dest="score_threshold",
        help="Manually set the score cutoff for inclusion in Top of WAYFT, defaults to {}".format(DEFAULT_SCORE_THRESHOLD),
        type='int',
        default=DEFAULT_SCORE_THRESHOLD
    )
    parser.add_option(
        "-l",
        "--run_length",
        dest="run_length",
        choices=[RunLength.MONTH, RunLength.YEAR],
        help="How long should the scraper run for?",
        default=RunLength.MONTH
    )
    (options, args) = parser.parse_args()

    scraper = WAYFTScraper()

    scraper.scrape(
        score_threshold=options.score_threshold,
        run_length=options.run_length,
        month=int(options.month),
        year=int(options.year)
    )