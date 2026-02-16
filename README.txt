F3L CONTEST SERIES WEBSITE - SETUP INSTRUCTIONS
===============================================

IMPORTANT: Assets Folder Setup
-------------------------------

To complete the website setup, you need to create an 'assets' folder and add your files:

1. Create a folder named 'assets' in the same directory as your HTML files:
   
   Your website structure should look like:
   /your-website-folder/
   ├── index.html
   ├── schedule.html
   ├── results.html
   ├── about.html
   ├── howto.html
   ├── host.html
   ├── styles.css
   └── assets/
       └── F3L contest bulletin template 2026 v1.1.doc

2. Place your document "F3L contest bulletin template 2026 v1.1.doc" 
   in the assets folder

3. The download link on the "Host a Contest" page will then work correctly

File Organization Tips:
-----------------------
- Keep all images in the assets folder (when you add them)
- If you add more downloadable files (PDFs, forms, etc.), put them in assets
- Keep the main directory clean with just the HTML and CSS files

Testing Locally:
----------------
After adding the assets folder:
1. Open index.html in Chrome
2. Navigate to "Host a Contest" tab
3. Click "Join the Series" tab
4. Test the download button for the contest bulletin template

When Uploading to AWS S3 or Apache:
------------------------------------
Make sure to upload the entire assets folder along with all HTML/CSS files.
The folder structure must be maintained for download links to work.

Questions?
----------
Contact: info@F3Lcontestseries.org
