#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import Select
from selenium.webdriver.firefox.options import Options

from PIL import Image, ImageDraw, ImageFont

from functools import partial

import time, sys


print = partial(print, flush = True)

def make_options():
    options = Options()
    options.headless = True
    return options

def create_driver():
    driver = webdriver.Firefox(options=make_options())
    driver.set_window_size(3000, 3000)
    return driver

def force_wait(driver, time):
    try:
        WebDriverWait(driver, time).until(
            lambda driver: driver.execute_script("return false"))
    except TimeoutException:
        pass

def locator(driver, booth):
    script = """ //
    var booth_object = vectorLayer.getSource().getFeatureById("{}");
    var mco = booth_object.get("internalExtentUnrotated");
    var centered_x = (mco[0] + mco[2]) / 2;
    var centered_y = (mco[1] + mco[3]) / 2;
    var point = [centered_x, centered_y];
    //var point_ar = booth_object.getGeometry().getCoordinates()[0];
    var pixel = map.getPixelFromCoordinate(point);
    return pixel;""".format(booth)
    return driver.execute_script(script)

def get_bounding(driver, xpath):
    script = """ //
    // Note: grabbed from stack overflow
    // https://stackoverflow.com/questions/10596417/is-there-a-way-to-get-element-by-xpath-using-javascript-in-selenium-webdriver
    function getElementByXpath(path) {{
      return document.evaluate(path, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
    }}
    var e = getElementByXpath('{}');
    return e.getBoundingClientRect();
    """.format(xpath)
    return driver.execute_script(script)

def create_floormap(driver, site, query, tries=0):
    if (tries >= 3): 
        exit()

    print( 'Loading site...')
    driver.get(site)
    driver.implicitly_wait(5);

    print( 'Searching for "{}"'.format(query))
    driver.find_element(By.ID, "jq-search-query").send_keys(query)
    driver.find_element(By.ID, "jq-mainSearchButton").click()

    print( 'Loading floormap...')
    force_wait(driver, 2)

    # is there an exhibitors and categories tab as well?
    category_check = driver.find_elements(By.XPATH, '//*[@id="jq-myssearchresults"]')
    child_count = category_check[0].find_elements(By.XPATH, "*")
    if len(child_count) > 2:
        driver.find_element(By.XPATH, '//*[@id="jq-section-exhibitorkeyword"]/a').click();

    force_wait(driver, 3)

    # load the floormap
    driver.find_element(By.XPATH, '//*[@id="jq-section-exhibitorkeyword"]/div/div/div/div/div[1]/div/a').click()
    force_wait(driver, 3)

    halls = driver.find_element(By.XPATH, '//*[@id="hallIDSelect"]').find_elements(By.XPATH, '*')
    hall_select = Select(driver.find_element(By.XPATH, '//*[@id="hallIDSelect"]'))

    print( 'Found {} halls...'.format(len(halls)))
    print('@!{}h'.format(len(halls)))
    for i in range(0, len(halls)):
        print( 'Selected hall {}'.format(i))
        hall_select.select_by_index(i)
        force_wait(driver, 8)

        print( 'Locating booth brands and numbers...')
        search_hit_root_xpath = '//*[@id="matchingExhibitorsTable"]/tbody/tr'
        search_hit_results = driver.find_elements(By.XPATH, search_hit_root_xpath)
        print('Found {} results...'.format(len(search_hit_results)))
        if (len(search_hit_results) == 0):
            print( 'No hits found.')
        else:
            count = 1
            brands = {}
            for row in search_hit_results:
                # in form of "(5252A)"
                number_xpath = search_hit_root_xpath + "[{}]/td[2]/span".format(count)
                brand_xpath = search_hit_root_xpath + "[{}]/td[2]/a".format(count)
                booth_number = driver.find_element(By.XPATH, number_xpath).text
                booth_brand = driver.find_element(By.XPATH, brand_xpath).text
                if (booth_brand != '' and booth_number != ''):
                    brands[booth_brand] = booth_number[1:-1]
                    print_string = "  " + booth_brand + " " + booth_number[1:-1]
                    print( print_string)
                count += 1

            map_bounds = get_bounding(driver, '//*[@id="mys-floorplan-canvas-div"]/div[3]/canvas')

            print('Taking screenshot...')
            driver.get_screenshot_as_file("screen.png")
            image = Image.open("screen.png")
            draw  = ImageDraw.Draw(image)
            font  = ImageFont.truetype("DejaVuSans.ttf", 24)
            smallfont  = ImageFont.truetype("DejaVuSans.ttf", 24)

            print( 'Drawing on map...')
            count = 1
            successes = 0
            for brand, number in brands.items():
                try:
                    coords = locator(driver, number)
                    size = 15
                    x0 = coords[0] - size
                    x1 = coords[0] + size
                    y0 = coords[1] - size + map_bounds['top']
                    y1 = coords[1] + size + map_bounds['top']
                    draw.rectangle( [x0, y0, x1, y1], "#ffff00", "#000000")
                    draw.text(
                        (coords[0] - size + (size / 8), coords[1] - size + (size / 8) + map_bounds['top']), 
                        repr(count), 
                        "#000000", 
                        font)

                    w = 700
                    h = 32
                    x = map_bounds['width'] - w - 50
                    y = h * count + ((map_bounds['bottom']) - (h * (len(brands) + 2)))
                    draw.rectangle( [x, y, x+w, y+h], "#ffffff", "#000000")
                    draw.text((x+6, y+2), "{}) {} ({})".format(count, brand, number), "#000000", smallfont)
                    successes += 1
                except:
                    pass
                finally:
                    count += 1
            if successes > 0:
                print( 'Cropping and saving the final result...')
                image.crop(
                        (0, map_bounds['top'], map_bounds['width'], map_bounds['bottom'])
                        ).save("./outputs/result-{}-{}.png".format(query, i))
                time.sleep(2)
                print("@@{}\n\n".format("./outputs/result-{}-{}.png".format(query, i)))
                print( 'Done!')
            else:
                print( 'Moving on...')
    driver.quit()

create_floormap(create_driver(), sys.argv[1], sys.argv[2])
# Code mostly uses openLayers.
#
# var x = vectorLayer.getSource.getFeatureById(booth#)
# var y = x.get("internalExtentUnrotated")
# var px = (y[0] + y[2]) / 2;
# var py = (y[1] + y[3]) / 2;
# var point = map.getPixelFromCoordinate([px, py]);

