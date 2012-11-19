#!/usr/bin/python
# -*- coding: utf-8 -*-

# TODO: Add copyright notice here


from urllib2 import HTTPError
import datetime
import logging
import unittest

import isotropic
import utils


# Module-level logging instance
log = logging.getLogger(__name__)


class IsotropicScraper(unittest.TestCase):
    def test_rawgames_functions(self):
        """Validate IsotropicScraper for raw games"""

        # Careful, as right now this touches bits of production, such
        # as the S3 buckets.

        # TODO: Figure out how to get this pointed at a database for
        # use in integration tests.

        iso = isotropic.IsotropicScraper(None)

        self.assertEquals(iso.our_gamelog_filename(datetime.date(2010, 10, 15)),
                          "20101015.all.tar.bz2")
        self.assertEquals(iso.our_gamelog_filename(datetime.date(2010, 3, 7)),
                          "20100307.all.tar.bz2")

        self.assertEquals(iso.isotropic_rawgame_url(datetime.date(2010, 10, 15)),
                          "http://dominion.isotropic.org/gamelog/201010/15/all.tar.bz2")
        self.assertEquals(iso.isotropic_rawgame_url(datetime.date(2010, 3, 7)),
                          "http://dominion.isotropic.org/gamelog/201003/07/all.tar.bz2")

        self.assertEquals(iso.s3_rawgame_url(datetime.date(2010, 10, 15)),
                          "http://static.councilroom.mccllstr.com/scrape_data/20101015.all.tar.bz2")
        self.assertEquals(iso.s3_rawgame_url(datetime.date(2010, 3, 7)),
                          "http://static.councilroom.mccllstr.com/scrape_data/20100307.all.tar.bz2")


    def test_rawgames_integration(self):
        """Validate IsotropicScraper for raw games"""

        # Careful, as right now this touches bits of production, such
        # as the S3 buckets.

        # TODO: Figure out how to get this pointed at a database for
        # use in integration tests.

        iso = isotropic.IsotropicScraper(utils.get_mongo_database())

        self.assertTrue(iso.is_rawgames_in_s3(datetime.date(2010, 10, 15)))

        self.assertRaisesRegexp(HTTPError, 'HTTP Error 404: Not Found',
                                iso.copy_rawgames_to_s3, datetime.date(2009, 10, 15))

        content = iso.get_rawgames_from_s3(datetime.date(2010, 10, 15))
        self.assertEquals(content[0:7], 'BZh91AY', "Tar file signature")

        # TODO: Figure out how to run the lengthy tests that hit
        # actual files on Isotropic only in certain limited modes
        if None:
            iso.copy_rawgames_to_s3(datetime.date(2012, 10, 3))

            # Scrape and insert a whole gameday
            iso.scrape_and_store_rawgames(datetime.date(2012, 9, 15))


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
