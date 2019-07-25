# Guangzhou-Green-Data-Collection
Green Data is a non-profit organization that focuses on public supervision towards environmental issues. This project is what I built when I had the web-scrawling internship there in 2019. Mostly I helped my boss build or improved the scrawling robots over and over again, because we constantly encountered a bunch of situations that we had never expected. 

  My boss and I were in charge of the environmental effects of construction projects. What we needed to do is scrape the information from as many reports as possible which were supposed to be posted on the municipal official websites. And our target is to code a crawler which is able to be applied as widely as possible. In other words, we should take as many circumstances as possible into consideration. One obvious example: in the first few days I worked in Green Data, since I preferred "xpath" method of location, I often simply clicked the "Copy XPath" without a second thought. Such a lazy behavior turned out to be a huge trouble when I or Boss transferred the codes to another city's municipal website, due to the fact that the index of a certain tab, for instance especially \<td> or \<li>, is not always the same. So this experience told us that it is never right to be lazy and I should figure out the general patterns among all the web pages over China.
  
So now I will show you what I figured out and hope somebody to help me improve all the stuff.

At this stage, you will see a lot changes in our methodology. But flaws still existed. So soon we abandoned the functions either.
