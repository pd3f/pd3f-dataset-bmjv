# pd3f-dataset-bmjv 

Dataset of (mostly German) PDFs used to develop [pd3f](https://github.com/pd3f).

This repository contains the code to scrape and download some public documents (PDFs). The can files be downloaded here: <https://data.jfilter.de/nlp/pd3f/bmjv_v1.zip>.

## Origin of the Dataset

1. Downloaded "Stellungnahmen zu Referententwürfen" from the [BMJV](https://www.bmjv.de/SiteGlobals/Forms/Suche/Gesetzgebungsverfahrensuche_Formular.html?resultsPerPage=25), around 02.04.2022
2. Prepend filenames with numbers
3. OCRd for German and English with OCRmyPDF
4. Sort / group by language
5. Redo broken OCR (manually detecting errors while working on the PDFs) 

## License

GPLv3
