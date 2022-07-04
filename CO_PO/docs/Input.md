### Help - Input Format
---

#### Workbook Format


1. `.xlsx` format is required (**NOTE:.`xls` format will not be accepted.**)
   
2. Workbook can have any number of sheets. Bu last few sheets are considered in which the format of tables and contents inside it will be used for processing for output. For more information regarding the format, Please refer to the `Introduction` Sheet of this [Sample Input File](../assets/Sample%20Input.xlsx).
   
3. There are no issues until now with the size of file. Application accepts any acceptable format of size under 1GB.

---

#### Number of Exams

1. In the Workbook, last few sheets are considered which will be determined by this Input.
2. Can be any valid Integer from 1 to 100. _(let us know if range needs to be increased)_

---
### Processing

Data is processed only when File is given as Input along with Number of Exams

#### NOTE

* At a time in a single Server (which means after starting an instance of CO-PO Mapping), we can only **process a request once at time**. 
  
---

### Multiple Requests

There are two ways one could process two different requests 

1. `simultaneously` - For this open CO-PO Mapping.exe more than once. Run the requests in different server (notice their URLs are different).

2. `wait` - After processing a request, you can request another request in the same server.

---

## Wait until below window appears

![Window](../assets/Sample%20Output%20Image.jpg)