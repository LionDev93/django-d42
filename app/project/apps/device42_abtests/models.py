from __future__ import unicode_literals
from django.shortcuts import HttpResponse, render
from django.db import models


# Create your models here.

class Experiment(models.Model):
  def __str__(self):
    try:
      return self.name
    except:
      return 'experiment'
    """
    Simple A/B Experiment model
    """
    name = models.CharField(max_length=255, null=True, blank=True)

    def render(self, request, context):
      ex = self
      userTest = None
      if not request.COOKIES.get('e_' + str(ex.pk), ''):
        tests = ex.tests.all()
        if tests.count() > 0:
          userTest = tests[0]
          for test in tests:
            if test.hits < userTest.hits:
              userTest = test
          userTest.hits += 1
          userTest.save()
        else:
          raise Exception('No Tests For This Experiment')
      else:
        userTest = Test.objects.get(pk=request.COOKIES.get('e_' + str(ex.pk), ''))
      response = render(request, userTest.template_name, context)
      response.set_cookie('e_' + str(ex.pk), str(userTest.pk), max_age=3600 * 24 * 365)
      return response

    def getTemplateName(self, request, response):
      """
      This basically assigns everyone to a test for every experiment.  Tests are assigned into cookies.
      The cookie will have the name of e_13 meaning the experiment pk is 13 and the value of that cookie
      will be the pk of the test.   If the user doesn't have a cookie for an experiment then we assign them
      one based on whichever test in that experiment has the least number hits.
      """
      ex = self
      if not response:
        response = HttpResponse
      if not request.COOKIES.get('e_' + str(ex.pk), ''):
        tests = ex.tests.all()
        if tests.count() > 0:  # make sure there is a test
          usersTest = tests[0]  # usersTest is going to be the test with minimum hits
          for test in tests:
            if test.hits < usersTest.hits:
              usersTest = test
              response
              response.set_cookie('e_' + str(ex.pk), str(usersTest.pk), max_age=3600 * 24 * 365)
              usersTest.hits += 1
              usersTest.save()
        else:
          test = Test.objects.get(pk=request.COOKIES.get('e_' + str(ex.pk), ''))
        return test.template_name

      def achieveGoal(self, request, response):
        """
        This looks at the experiment and makes sure that it is the first time that they have achieved that
        experiment goal.  If it's the first time the user has reached the goal, then we increment the
        conversion counter for the test and set the achieved cookie for that experiment.
        """
        # check to see if we have hit any of our goals:
        ex = self
        if not request.COOKIES.get('achived_' + str(ex.pk), ''):  # make sure we haven't achieved this goal
          test_pk = request.COOKIES.get('e_' + str(ex.pk), '')
          if test_pk:
            print('reached a goal')
            test = ex.tests.get(pk=test_pk)
            test.conversions += 1
            test.save()
            response.set_cookie('achieved_' + str(ex.pk), 'yes', max_age=3600 * 24 * 365)


class Test(models.Model):
  experiment = models.ForeignKey(Experiment, related_name='tests')

  template_name = models.CharField(max_length=255,
                                   help_text="Example: 'signup_1.html'. The template to be tested.")
  hits = models.IntegerField(default=0,
                             help_text="# uniques that have seen this template.")
  conversions = models.IntegerField(default=0,
                                    help_text="# uniques that have reached the goal from this test.")

  def __str__(self):
    print('test test test test')
    try:
      return self.name
    except:
      return self.template_name
