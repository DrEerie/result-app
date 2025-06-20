__________________
#  Under Construction... Just as a free time activity... 
____________________
### Motivation: 
Actually Saw my aunt do manual work on her school result. So got and idea to create a result-app for schools ;) 
_________________

# What App Will Do
Wanna see following thnings in the app at the base: 
<ol>
<li> Teacher will Input Marks Manually (Won't accept from excel since typing in excel also requires manual entires so why not to directly enter in the app) </li>
 <li> Class drop-down so that subject will be automatically loaded for the mention class </li>
<li> Make the dynamic result on-time. Subject wise plus overall grading and percentage. </li> 
<li> Preview result online </li> 
<li>Generate Individual Marksheet Pluse Generate PDF Report for Each Class/ Section </li> 
<li> Save marks to DB </li>
 <li> Conformation Flash Message </li>
</ol>


# Current folder structure of project:
```
result-system/
├── templates/
│   ├── layout.html
│   ├── home.html
│   ├── enter_result.html
│   └── view_result.html
├── static/
│   ├── css/
│   │   └── tailwind.min.css  (CDN-linked via HTML)
│   └── js/
├── models/
│   └── models.py
├── forms/
│   └── result_forms.py
├── utils/
│   └── grading.py  (for % and grade logic)
├── database/
│   └── result.db  (SQLite for now)
├── app.py
├── requirements.txt
└── README.md

```
